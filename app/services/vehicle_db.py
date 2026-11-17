from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy import or_, and_
from ..models.entities import db, Vehicle, Booking
from ..models.exceptions import VehicleNotFoundError, InvalidStateTransitionError
from .green_cache import green_cache

class VehicleDB:
    """Vehicle data access and inventory manager with caching and green query optimization."""
    
    @classmethod
    def getVehicle(cls, vehicle_id: int, use_cache: bool = True) -> Optional[Vehicle]:
        """Fetch vehicle by ID with Green TTL caching."""
        cache_key = f"vehicle:{vehicle_id}"
        if use_cache:
            cached = green_cache.get(cache_key)
            if cached is not None:
                # Reconstruct or return cached instance dictionary/model
                # Return vehicle from DB or cached entity
                pass
                
        green_cache.record_db_read(1)
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle not found with ID: {vehicle_id}")
            
        if use_cache:
            green_cache.set(cache_key, vehicle.to_dict(full=True))
            
        return vehicle

    @classmethod
    def isVehicleAvailable(cls, vehicle_id: int, pickup_date: date, return_date: date) -> bool:
        """Check if vehicle is available for the given date range.
        CRITICAL: Prevents overlapping bookings!
        """
        vehicle = cls.getVehicle(vehicle_id, use_cache=False)
        if vehicle.Availability_Status in [Vehicle.STATE_UNDER_MAINTENANCE, Vehicle.STATE_RETIRED]:
            return False
            
        # Check active or confirmed overlapping bookings
        green_cache.record_db_read(1)
        overlapping_count = Booking.query.filter(
            Booking.Vehicle_ID == vehicle_id,
            Booking.Booking_Status.in_([Booking.STATUS_CONFIRMED, Booking.STATUS_ACTIVE]),
            Booking.Pickup_Date <= return_date,
            Booking.Return_Date >= pickup_date
        ).count()
        
        return overlapping_count == 0

    @classmethod
    def searchVehicle(cls, vehicle_type: Optional[str] = None) -> List[Vehicle]:
        """Find vehicles filtered by type."""
        green_cache.record_db_read(1)
        query = Vehicle.query
        if vehicle_type and vehicle_type.strip() and vehicle_type.lower() != "all":
            query = query.filter(Vehicle.Vehicle_Type.ilike(vehicle_type.strip()))
        return query.all()

    @classmethod
    def searchAvailableVehicles(
        cls, 
        pickup_date: Optional[date] = None, 
        return_date: Optional[date] = None, 
        vehicle_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 8,
        projection_only: bool = True
    ) -> dict:
        """Search available vehicles with pagination and selective field projection (Green computing)."""
        cache_key = f"search:{pickup_date}:{return_date}:{vehicle_type}:{page}:{page_size}:{projection_only}"
        cached = green_cache.get(cache_key)
        if cached:
            return cached

        green_cache.record_db_read(1)
        query = Vehicle.query.filter(
            Vehicle.Availability_Status.notin_([Vehicle.STATE_UNDER_MAINTENANCE, Vehicle.STATE_RETIRED])
        )

        if vehicle_type and vehicle_type.strip() and vehicle_type.lower() != "all":
            query = query.filter(Vehicle.Vehicle_Type.ilike(vehicle_type.strip()))

        # If date range is provided, exclude vehicles with overlapping bookings
        if pickup_date and return_date:
            subquery = db.session.query(Booking.Vehicle_ID).filter(
                Booking.Booking_Status.in_([Booking.STATUS_CONFIRMED, Booking.STATUS_ACTIVE]),
                Booking.Pickup_Date <= return_date,
                Booking.Return_Date >= pickup_date
            ).subquery()
            query = query.filter(~Vehicle.Vehicle_ID.in_(subquery))

        total_count = query.count()
        vehicles = query.offset((page - 1) * page_size).limit(page_size).all()
        
        items = [v.to_dict(full=not projection_only) for v in vehicles]
        
        result = {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
            "vehicles": items
        }
        
        green_cache.set(cache_key, result, ttl=30)
        return result

    @classmethod
    def addVehicle(
        cls, 
        registration_number: str, 
        model: str, 
        vehicle_type: str, 
        rental_rate: float, 
        current_odometer: float = 0.0,
        image_url: str = None,
        features: str = None
    ) -> Vehicle:
        """Add new vehicle to inventory."""
        if rental_rate <= 0:
            raise ValueError("Rental rate must be greater than 0.")
            
        vehicle = Vehicle(
            Registration_Number=registration_number.strip().upper(),
            Model=model.strip(),
            Vehicle_Type=vehicle_type.strip(),
            Rental_Rate=round(float(rental_rate), 2),
            Current_Odometer=current_odometer,
            Image_URL=image_url,
            Features=features,
            Availability_Status=Vehicle.STATE_AVAILABLE
        )
        db.session.add(vehicle)
        db.session.commit()
        green_cache.record_db_write(1)
        green_cache.invalidate("search:")
        return vehicle

    @classmethod
    def updateVehicle(
        cls, 
        vehicle_id: int, 
        model: str = None, 
        vehicle_type: str = None, 
        rental_rate: float = None, 
        availability_status: str = None,
        current_odometer: float = None,
        features: str = None
    ) -> Vehicle:
        """Update vehicle details."""
        vehicle = cls.getVehicle(vehicle_id, use_cache=False)
        if model:
            vehicle.Model = model.strip()
        if vehicle_type:
            vehicle.Vehicle_Type = vehicle_type.strip()
        if rental_rate is not None:
            if rental_rate <= 0:
                raise ValueError("Rental rate must be greater than 0.")
            vehicle.Rental_Rate = round(float(rental_rate), 2)
        if availability_status:
            if availability_status not in Vehicle.VALID_STATES:
                raise InvalidStateTransitionError(f"Invalid state: {availability_status}")
            vehicle.Availability_Status = availability_status
        if current_odometer is not None:
            vehicle.Current_Odometer = current_odometer
        if features is not None:
            vehicle.Features = features
            
        db.session.commit()
        green_cache.record_db_write(1)
        green_cache.invalidate(f"vehicle:{vehicle_id}")
        green_cache.invalidate("search:")
        return vehicle

    @classmethod
    def deactivateVehicle(cls, vehicle_id: int) -> Vehicle:
        """Deactivate/retire vehicle from fleet."""
        vehicle = cls.getVehicle(vehicle_id, use_cache=False)
        vehicle.retire_vehicle()
        db.session.commit()
        green_cache.record_db_write(1)
        green_cache.invalidate(f"vehicle:{vehicle_id}")
        green_cache.invalidate("search:")
        return vehicle
