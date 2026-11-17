from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from ..models.entities import db, Vehicle, Booking, Rental, Payment, Customer
from ..models.exceptions import (
    BookingNotFoundError,
    VehicleNotFoundError,
    VehicleUnavailableError,
    InvalidDurationError,
    PaymentFailedError,
    InvalidStateTransitionError
)
from .payment_gateway import PaymentGateway
from .vehicle_db import VehicleDB
from .green_cache import green_cache
from ..config import Config

class BookingService:
    """Core domain service for handling vehicle booking, payments, pickup, and return flows."""

    @staticmethod
    def calculateRent(daily_rate: float, days: int) -> float:
        """Calculate base rent for vehicle and given days.
        Constraint: days must be >= 1.
        """
        if days is None or days <= 0:
            raise InvalidDurationError("Invalid duration error: rental days must be >= 1.")
        if daily_rate is None or daily_rate <= 0:
            raise ValueError("Rental daily rate must be greater than 0.")
        return round(float(daily_rate) * int(days), 2)

    @classmethod
    def checkAvailability(cls, vehicle_id: int, pickup_date: date, return_date: date) -> bool:
        """Check if vehicle is available for the given timeframe without overlap."""
        return VehicleDB.isVehicleAvailable(vehicle_id, pickup_date, return_date)

    @classmethod
    def bookVehicle(
        cls,
        customer_id: int,
        vehicle_id: int,
        pickup_date: date,
        return_date: date,
        payment_method: str = "Credit Card",
        simulate_payment_failure: bool = False,
        amount_to_pay: Optional[float] = None,
        custom_booking_id: Optional[int] = None
    ) -> Booking:
        """Complete booking pipeline:
        1. Validate vehicle exists
        2. Validate availability (prevent overlapping bookings)
        3. Validate rental duration (days >= 1)
        4. Calculate charges
        5. Process payment through mock gateway (roll back if payment fails)
        6. Transition vehicle state Available -> Booked
        7. Persist booking and payment records
        """
        # Step 1: Check vehicle
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle not found with ID: {vehicle_id}")

        # Step 2: Check availability
        if not cls.checkAvailability(vehicle_id, pickup_date, return_date):
            raise VehicleUnavailableError(
                f"Vehicle '{vehicle.Model}' ({vehicle.Registration_Number}) is not available for the selected dates."
            )

        # Step 3: Validate duration
        if return_date <= pickup_date:
            raise InvalidDurationError("Invalid duration error: return date must be strictly after pickup date.")
        duration_days = (return_date - pickup_date).days
        if duration_days <= 0:
            raise InvalidDurationError("Invalid duration error: rental days must be >= 1.")

        # Step 4: Calculate total rent
        total_rent = cls.calculateRent(vehicle.Rental_Rate, duration_days)
        charge_amount = amount_to_pay if amount_to_pay is not None else total_rent

        # Step 5: Validate and process payment FIRST (Atomic guarantee: failure -> no booking created)
        if charge_amount <= 0:
            raise PaymentFailedError("Payment Failed: Amount must be greater than 0.")

        # Call payment gateway
        payment_result = PaymentGateway.makePayment(
            amount=charge_amount,
            method=payment_method,
            simulate_failure=simulate_payment_failure
        )

        try:
            # Step 6: Vehicle state machine transition Available -> Booked
            vehicle.book_vehicle()

            # Step 7: Create Booking
            booking_kwargs = {
                "Customer_ID": customer_id,
                "Vehicle_ID": vehicle_id,
                "Booking_Date": datetime.utcnow(),
                "Pickup_Date": pickup_date,
                "Return_Date": return_date,
                "Booking_Status": Booking.STATUS_CONFIRMED,
                "Total_Amount": total_rent,
                "Cancellation_Fee": 0.0
            }
            if custom_booking_id is not None:
                booking_kwargs["Booking_ID"] = custom_booking_id

            booking = Booking(**booking_kwargs)
            db.session.add(booking)
            db.session.flush() # Populate booking.Booking_ID

            # Step 8: Create Payment record linked to booking
            payment = Payment(
                Booking_ID=booking.Booking_ID,
                Rental_ID=None,
                Amount=charge_amount,
                Payment_Date=datetime.utcnow(),
                Payment_Method=payment_method,
                Payment_Status=Payment.STATUS_COMPLETED,
                Payment_Purpose="Booking Deposit",
                Transaction_Ref=payment_result["transaction_ref"]
            )
            db.session.add(payment)
            db.session.commit()

            green_cache.record_db_write(2)
            green_cache.invalidate("search:")
            green_cache.invalidate(f"vehicle:{vehicle_id}")
            return booking

        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def pickupVehicle(
        cls,
        booking_id: int,
        staff_id: Optional[int] = None,
        start_odometer: Optional[float] = None
    ) -> Rental:
        """Process vehicle pickup by rental staff.
        Transitions:
        - Vehicle state: Booked -> Rented
        - Booking status: Confirmed -> Active
        - Creates Rental record
        """
        booking = Booking.query.get(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Booking not found with ID: {booking_id}")

        if booking.Booking_Status != Booking.STATUS_CONFIRMED:
            raise VRMSError(f"Cannot pickup vehicle: booking status is '{booking.Booking_Status}'. Expected 'Confirmed'.")

        vehicle = booking.vehicle
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle associated with booking {booking_id} not found.")

        # State transition: Booked -> Rented
        vehicle.pickup_vehicle()

        odo = start_odometer if start_odometer is not None else vehicle.Current_Odometer

        rental = Rental(
            Booking_ID=booking.Booking_ID,
            Actual_Pickup_Date=datetime.utcnow(),
            Start_Odometer=odo,
            Rental_Duration=booking.duration_days,
            Extra_Charges=0.0,
            Late_Fee=0.0,
            Damage_Fee=0.0
        )
        booking.Booking_Status = Booking.STATUS_ACTIVE

        db.session.add(rental)
        db.session.commit()

        green_cache.record_db_write(2)
        green_cache.invalidate(f"vehicle:{vehicle.Vehicle_ID}")
        green_cache.invalidate("search:")
        return rental

    @classmethod
    def returnVehicle(
        cls,
        booking_id: int,
        staff_id: Optional[int] = None,
        end_odometer: Optional[float] = None,
        damage_fee: float = 0.0,
        damage_notes: Optional[str] = None,
        actual_return_date: Optional[datetime] = None,
        payment_method: str = "Credit Card",
        simulate_payment_failure: bool = False
    ) -> Dict[str, Any]:
        """UC-08 Return Vehicle Flow:
        1. Staff enters Booking ID -> load booking, vehicle, and rental.
        2. Staff verifies condition and odometer reading.
        3. Calculate charges:
           - Late return fine (if actual_return_date > scheduled return_date)
           - Damage charge (if damage_fee > 0)
        4. Customer pays remaining balance (retry on payment failure).
        5. Vehicle state transition:
           - If damage_fee > 0: Rented -> Under Maintenance
           - Else: Rented -> Available
        6. Booking status set to Completed.
        7. Generate itemized return receipt.
        """
        booking = Booking.query.get(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Booking not found with ID: {booking_id}")

        rental = booking.rental
        if not rental:
            raise VRMSError(f"No active rental record found for booking {booking_id}.")

        vehicle = booking.vehicle
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle associated with booking {booking_id} not found.")

        actual_return = actual_return_date or datetime.utcnow()
        scheduled_return = datetime.combine(booking.Return_Date, datetime.min.time())

        # Alternate flow 5a: Late return fine calculation
        late_fee = 0.0
        late_days = 0
        if actual_return.date() > booking.Return_Date:
            late_days = (actual_return.date() - booking.Return_Date).days
            # 1.5x daily rate per late day
            late_fee = round(late_days * (vehicle.Rental_Rate * Config.LATE_FEE_MULTIPLIER), 2)

        # Alternate flow 5b: Damage charge
        clean_damage_fee = round(max(0.0, float(damage_fee)), 2)
        total_extra_charges = round(late_fee + clean_damage_fee, 2)

        # Total cost and remaining balance calculation
        total_contract_amount = round(booking.Total_Amount + total_extra_charges, 2)
        total_already_paid = round(sum(p.Amount for p in booking.payments if p.Payment_Status == Payment.STATUS_COMPLETED), 2)
        remaining_balance = round(max(0.0, total_contract_amount - total_already_paid), 2)

        # Process payment for remaining balance if > 0
        payment_record = None
        if remaining_balance > 0:
            payment_resp = PaymentGateway.makePayment(
                amount=remaining_balance,
                method=payment_method,
                simulate_failure=simulate_payment_failure
            )
            payment_record = Payment(
                Booking_ID=booking.Booking_ID,
                Rental_ID=rental.Rental_ID,
                Amount=remaining_balance,
                Payment_Date=datetime.utcnow(),
                Payment_Method=payment_method,
                Payment_Status=Payment.STATUS_COMPLETED,
                Payment_Purpose="Return Settlement",
                Transaction_Ref=payment_resp["transaction_ref"]
            )
            db.session.add(payment_record)

        # Odometer update
        if end_odometer is not None:
            if end_odometer < rental.Start_Odometer:
                raise ValueError(f"End odometer ({end_odometer}) cannot be less than start odometer ({rental.Start_Odometer}).")
            rental.End_Odometer = end_odometer
            vehicle.Current_Odometer = end_odometer

        # State transition:
        # If damage reported -> Under Maintenance; Else -> Available
        if clean_damage_fee > 0:
            vehicle.report_damage()
        else:
            vehicle.return_vehicle()

        # Update Rental and Booking
        rental.Actual_Return_Date = actual_return
        rental.Late_Fee = late_fee
        rental.Damage_Fee = clean_damage_fee
        rental.Extra_Charges = total_extra_charges
        rental.Damage_Notes = damage_notes

        booking.Booking_Status = Booking.STATUS_COMPLETED
        db.session.commit()

        green_cache.record_db_write(2)
        green_cache.invalidate(f"vehicle:{vehicle.Vehicle_ID}")
        green_cache.invalidate("search:")

        # Generate return receipt
        receipt = {
            "receipt_id": f"RCPT-{rental.Rental_ID:05d}-{booking.Booking_ID}",
            "receipt_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "booking_id": booking.Booking_ID,
            "rental_id": rental.Rental_ID,
            "customer": {
                "id": booking.customer.Customer_ID,
                "name": booking.customer.Customer_Name,
                "email": booking.customer.Email,
                "phone": booking.customer.Phone,
                "license": booking.customer.License_Number
            },
            "vehicle": {
                "id": vehicle.Vehicle_ID,
                "model": vehicle.Model,
                "registration": vehicle.Registration_Number,
                "rate": vehicle.Rental_Rate,
                "status": vehicle.Availability_Status
            },
            "rental_period": {
                "scheduled_pickup": booking.Pickup_Date.strftime("%Y-%m-%d"),
                "scheduled_return": booking.Return_Date.strftime("%Y-%m-%d"),
                "actual_pickup": rental.Actual_Pickup_Date.strftime("%Y-%m-%d %H:%M"),
                "actual_return": rental.Actual_Return_Date.strftime("%Y-%m-%d %H:%M"),
                "late_days": late_days
            },
            "odometer": {
                "start": rental.Start_Odometer,
                "end": rental.End_Odometer,
                "distance_traveled": round((rental.End_Odometer - rental.Start_Odometer), 1) if rental.End_Odometer else 0.0
            },
            "financial_breakdown": {
                "base_rental_amount": booking.Total_Amount,
                "late_fee": late_fee,
                "damage_fee": clean_damage_fee,
                "total_extra_charges": total_extra_charges,
                "grand_total": total_contract_amount,
                "initial_deposit": total_already_paid,
                "settlement_paid": remaining_balance,
                "total_paid": round(total_already_paid + remaining_balance, 2),
                "remaining_due": 0.0,
                "payment_method": payment_method,
                "transaction_ref": payment_record.Transaction_Ref if payment_record else "N/A"
            },
            "damage_notes": damage_notes or "None"
        }
        return receipt

    @classmethod
    def cancelBooking(cls, booking_id: int, customer_id: Optional[int] = None) -> Booking:
        """Cancel a booking according to cancellation policy.
        Calculates cancellation fee and frees up vehicle.
        """
        booking = Booking.query.get(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Booking not found with ID: {booking_id}")

        if customer_id and booking.Customer_ID != customer_id:
            raise VRMSError("Unauthorized to cancel this booking.")

        if booking.Booking_Status != Booking.STATUS_CONFIRMED:
            raise VRMSError(f"Cannot cancel booking with status '{booking.Booking_Status}'.")

        # Cancellation fee calculation: 10% of base rent
        cancel_fee = round(booking.Total_Amount * (Config.CANCELLATION_FEE_PERCENT / 100.0), 2)
        booking.Cancellation_Fee = cancel_fee
        booking.Booking_Status = Booking.STATUS_CANCELLED

        # Return vehicle to Available if it was Booked
        vehicle = booking.vehicle
        if vehicle and vehicle.Availability_Status == Vehicle.STATE_BOOKED:
            # Check if other active booking exists for this vehicle right now
            other_active = Booking.query.filter(
                Booking.Vehicle_ID == vehicle.Vehicle_ID,
                Booking.Booking_ID != booking.Booking_ID,
                Booking.Booking_Status.in_([Booking.STATUS_CONFIRMED, Booking.STATUS_ACTIVE])
            ).count()
            if other_active == 0:
                vehicle.Availability_Status = Vehicle.STATE_AVAILABLE

        # Issue simulated refund for initial payment minus cancellation fee
        initial_payments = [p for p in booking.payments if p.Payment_Status == Payment.STATUS_COMPLETED]
        total_paid = sum(p.Amount for p in initial_payments)
        refund_amount = round(max(0.0, total_paid - cancel_fee), 2)

        if refund_amount > 0 and initial_payments:
            PaymentGateway.refundPayment(initial_payments[0].Transaction_Ref or "TXN-INIT", refund_amount)
            refund_record = Payment(
                Booking_ID=booking.Booking_ID,
                Amount=refund_amount,
                Payment_Date=datetime.utcnow(),
                Payment_Method="Refund",
                Payment_Status=Payment.STATUS_REFUNDED,
                Payment_Purpose="Cancellation Refund",
                Transaction_Ref=f"REF-{booking.Booking_ID}"
            )
            db.session.add(refund_record)

        db.session.commit()
        green_cache.record_db_write(2)
        green_cache.invalidate(f"vehicle:{booking.Vehicle_ID}")
        green_cache.invalidate("search:")
        return booking
