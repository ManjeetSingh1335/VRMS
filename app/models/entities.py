from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index
from .exceptions import InvalidStateTransitionError, InvalidDurationError

db = SQLAlchemy()

class Customer(db.Model):
    __tablename__ = "customer"
    
    Customer_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Customer_Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    Phone = db.Column(db.String(20), nullable=False)
    Address = db.Column(db.Text, nullable=False)
    License_Number = db.Column(db.String(50), nullable=False)
    Password_Hash = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.String(20), nullable=False, default="Customer") # Customer, Administrator, Rental Staff
    Created_At = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship("Booking", back_populates="customer", cascade="all, delete-orphan")
    
    def set_password(self, password: str) -> None:
        self.Password_Hash = generate_password_hash(password)
        
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.Password_Hash, password)
        
    def to_dict(self) -> dict:
        return {
            "Customer_ID": self.Customer_ID,
            "Customer_Name": self.Customer_Name,
            "Email": self.Email,
            "Phone": self.Phone,
            "Address": self.Address,
            "License_Number": self.License_Number,
            "Role": self.Role
        }


class Administrator(Customer):
    """Domain model subclass for Administrator."""
    __mapper_args__ = {
        'polymorphic_identity': 'Administrator',
    }


class RentalStaff(Customer):
    """Domain model subclass for Rental Staff."""
    __mapper_args__ = {
        'polymorphic_identity': 'Rental Staff',
    }


class Vehicle(db.Model):
    __tablename__ = "vehicle"
    __table_args__ = (
        CheckConstraint("Rental_Rate > 0", name="check_rental_rate_positive"),
        Index("idx_vehicle_status_type", "Availability_Status", "Vehicle_Type"),
    )
    
    # Valid States
    STATE_AVAILABLE = "Available"
    STATE_BOOKED = "Booked"
    STATE_RENTED = "Rented"
    STATE_UNDER_MAINTENANCE = "Under Maintenance"
    STATE_RETIRED = "Retired"
    
    VALID_STATES = {
        STATE_AVAILABLE,
        STATE_BOOKED,
        STATE_RENTED,
        STATE_UNDER_MAINTENANCE,
        STATE_RETIRED
    }
    
    Vehicle_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Registration_Number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    Model = db.Column(db.String(100), nullable=False)
    Vehicle_Type = db.Column(db.String(50), nullable=False, index=True) # Sedan, SUV, Hatchback, Luxury, Truck
    Rental_Rate = db.Column(db.Float, nullable=False)
    Availability_Status = db.Column(db.String(30), nullable=False, default=STATE_AVAILABLE, index=True)
    Current_Odometer = db.Column(db.Float, nullable=False, default=0.0)
    Image_URL = db.Column(db.String(255), nullable=True)
    Features = db.Column(db.String(255), nullable=True) # e.g. "Automatic, 5-seater, AC, GPS"
    
    # Relationships
    bookings = db.relationship("Booking", back_populates="vehicle", cascade="all, delete-orphan")
    
    # Vehicle State Machine Methods
    def book_vehicle(self) -> None:
        """Transition: Available -> Booked"""
        if self.Availability_Status != self.STATE_AVAILABLE:
            raise InvalidStateTransitionError(
                f"Cannot book vehicle: current status is '{self.Availability_Status}'. Expected '{self.STATE_AVAILABLE}'."
            )
        self.Availability_Status = self.STATE_BOOKED

    def pickup_vehicle(self) -> None:
        """Transition: Booked -> Rented"""
        if self.Availability_Status != self.STATE_BOOKED:
            raise InvalidStateTransitionError(
                f"Cannot pickup vehicle: current status is '{self.Availability_Status}'. Expected '{self.STATE_BOOKED}'."
            )
        self.Availability_Status = self.STATE_RENTED

    def return_vehicle(self) -> None:
        """Transition: Rented -> Available"""
        if self.Availability_Status != self.STATE_RENTED:
            raise InvalidStateTransitionError(
                f"Cannot return vehicle: current status is '{self.Availability_Status}'. Expected '{self.STATE_RENTED}'."
            )
        self.Availability_Status = self.STATE_AVAILABLE

    def report_damage(self) -> None:
        """Transition: Rented -> Under Maintenance"""
        if self.Availability_Status != self.STATE_RENTED:
            raise InvalidStateTransitionError(
                f"Cannot report damage: current status is '{self.Availability_Status}'. Expected '{self.STATE_RENTED}'."
            )
        self.Availability_Status = self.STATE_UNDER_MAINTENANCE

    def complete_maintenance(self) -> None:
        """Transition: Under Maintenance -> Available"""
        if self.Availability_Status != self.STATE_UNDER_MAINTENANCE:
            raise InvalidStateTransitionError(
                f"Cannot complete maintenance: current status is '{self.Availability_Status}'. Expected '{self.STATE_UNDER_MAINTENANCE}'."
            )
        self.Availability_Status = self.STATE_AVAILABLE

    def retire_vehicle(self) -> None:
        """Transition: Available -> Retired"""
        if self.Availability_Status != self.STATE_AVAILABLE:
            raise InvalidStateTransitionError(
                f"Cannot retire vehicle: current status is '{self.Availability_Status}'. Expected '{self.STATE_AVAILABLE}'."
            )
        self.Availability_Status = self.STATE_RETIRED

    def calculateRent(self, days: int) -> float:
        """Calculate base rent for given duration in days."""
        if days is None or days <= 0:
            raise InvalidDurationError("Invalid duration error: rental days must be >= 1.")
        return round(float(self.Rental_Rate) * float(days), 2)

    def to_dict(self, full: bool = True) -> dict:
        """Selective field projection for Green Software optimization."""
        base = {
            "Vehicle_ID": self.Vehicle_ID,
            "Registration_Number": self.Registration_Number,
            "Model": self.Model,
            "Vehicle_Type": self.Vehicle_Type,
            "Rental_Rate": self.Rental_Rate,
            "Availability_Status": self.Availability_Status,
        }
        if full:
            base.update({
                "Current_Odometer": self.Current_Odometer,
                "Image_URL": self.Image_URL or f"https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=500&auto=format&fit=crop&q=60",
                "Features": self.Features or "Automatic, AC, Airbags"
            })
        return base


class Booking(db.Model):
    __tablename__ = "booking"
    __table_args__ = (
        CheckConstraint("Return_Date > Pickup_Date", name="check_return_after_pickup"),
        Index("idx_booking_dates", "Pickup_Date", "Return_Date"),
        Index("idx_booking_vehicle_status", "Vehicle_ID", "Booking_Status"),
    )
    
    STATUS_CONFIRMED = "Confirmed"
    STATUS_ACTIVE = "Active"
    STATUS_COMPLETED = "Completed"
    STATUS_CANCELLED = "Cancelled"
    
    Booking_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Customer_ID = db.Column(db.Integer, db.ForeignKey("customer.Customer_ID"), nullable=False)
    Vehicle_ID = db.Column(db.Integer, db.ForeignKey("vehicle.Vehicle_ID"), nullable=False)
    Booking_Date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    Pickup_Date = db.Column(db.Date, nullable=False)
    Return_Date = db.Column(db.Date, nullable=False)
    Booking_Status = db.Column(db.String(30), nullable=False, default=STATUS_CONFIRMED)
    Total_Amount = db.Column(db.Float, nullable=False)
    Cancellation_Fee = db.Column(db.Float, default=0.0)
    
    # Relationships
    customer = db.relationship("Customer", back_populates="bookings")
    vehicle = db.relationship("Vehicle", back_populates="bookings")
    rental = db.relationship("Rental", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    
    @property
    def duration_days(self) -> int:
        if self.Return_Date and self.Pickup_Date:
            return (self.Return_Date - self.Pickup_Date).days
        return 0

    def to_dict(self) -> dict:
        total_paid = sum(p.Amount for p in self.payments if p.Payment_Status == "Completed")
        return {
            "Booking_ID": self.Booking_ID,
            "Customer_ID": self.Customer_ID,
            "Customer_Name": self.customer.Customer_Name if self.customer else None,
            "Customer_Email": self.customer.Email if self.customer else None,
            "Customer_Phone": self.customer.Phone if self.customer else None,
            "Vehicle_ID": self.Vehicle_ID,
            "Vehicle_Model": self.vehicle.Model if self.vehicle else None,
            "Vehicle_Registration": self.vehicle.Registration_Number if self.vehicle else None,
            "Vehicle_Type": self.vehicle.Vehicle_Type if self.vehicle else None,
            "Rental_Rate": self.vehicle.Rental_Rate if self.vehicle else 0,
            "Booking_Date": self.Booking_Date.strftime("%Y-%m-%d %H:%M") if self.Booking_Date else None,
            "Pickup_Date": self.Pickup_Date.strftime("%Y-%m-%d") if self.Pickup_Date else None,
            "Return_Date": self.Return_Date.strftime("%Y-%m-%d") if self.Return_Date else None,
            "Duration_Days": self.duration_days,
            "Booking_Status": self.Booking_Status,
            "Total_Amount": self.Total_Amount,
            "Total_Paid": round(total_paid, 2),
            "Cancellation_Fee": self.Cancellation_Fee,
            "Rental_ID": self.rental.Rental_ID if self.rental else None
        }


class Rental(db.Model):
    __tablename__ = "rental"
    
    Rental_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Booking_ID = db.Column(db.Integer, db.ForeignKey("booking.Booking_ID"), unique=True, nullable=False)
    Actual_Pickup_Date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    Actual_Return_Date = db.Column(db.DateTime, nullable=True)
    Rental_Duration = db.Column(db.Integer, nullable=True) # Duration in days
    Extra_Charges = db.Column(db.Float, nullable=False, default=0.0) # Sum of late fee and damage fee
    Start_Odometer = db.Column(db.Float, nullable=False, default=0.0)
    End_Odometer = db.Column(db.Float, nullable=True)
    Late_Fee = db.Column(db.Float, nullable=False, default=0.0)
    Damage_Fee = db.Column(db.Float, nullable=False, default=0.0)
    Damage_Notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    booking = db.relationship("Booking", back_populates="rental")
    payments = db.relationship("Payment", back_populates="rental", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        total_paid = sum(p.Amount for p in self.payments if p.Payment_Status == "Completed")
        initial_booking_paid = sum(p.Amount for p in self.booking.payments if p.Payment_Status == "Completed") if self.booking else 0.0
        all_paid = round(total_paid + initial_booking_paid, 2)
        grand_total = round((self.booking.Total_Amount if self.booking else 0.0) + self.Extra_Charges, 2)
        remaining = round(max(0.0, grand_total - all_paid), 2)
        
        return {
            "Rental_ID": self.Rental_ID,
            "Booking_ID": self.Booking_ID,
            "Actual_Pickup_Date": self.Actual_Pickup_Date.strftime("%Y-%m-%d %H:%M") if self.Actual_Pickup_Date else None,
            "Actual_Return_Date": self.Actual_Return_Date.strftime("%Y-%m-%d %H:%M") if self.Actual_Return_Date else None,
            "Rental_Duration": self.Rental_Duration,
            "Start_Odometer": self.Start_Odometer,
            "End_Odometer": self.End_Odometer,
            "Late_Fee": self.Late_Fee,
            "Damage_Fee": self.Damage_Fee,
            "Extra_Charges": self.Extra_Charges,
            "Damage_Notes": self.Damage_Notes,
            "Base_Amount": self.booking.Total_Amount if self.booking else 0.0,
            "Grand_Total": grand_total,
            "Total_Paid": all_paid,
            "Remaining_Balance": remaining,
            "Vehicle_Model": self.booking.vehicle.Model if self.booking and self.booking.vehicle else None,
            "Vehicle_Registration": self.booking.vehicle.Registration_Number if self.booking and self.booking.vehicle else None,
            "Customer_Name": self.booking.customer.Customer_Name if self.booking and self.booking.customer else None,
        }


class Payment(db.Model):
    __tablename__ = "payment"
    __table_args__ = (
        CheckConstraint("Amount > 0", name="check_payment_amount_positive"),
        Index("idx_payment_status", "Payment_Status"),
    )
    
    STATUS_COMPLETED = "Completed"
    STATUS_FAILED = "Failed"
    STATUS_REFUNDED = "Refunded"
    STATUS_PENDING = "Pending"
    
    Payment_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Booking_ID = db.Column(db.Integer, db.ForeignKey("booking.Booking_ID"), nullable=True)
    Rental_ID = db.Column(db.Integer, db.ForeignKey("rental.Rental_ID"), nullable=True)
    Amount = db.Column(db.Float, nullable=False)
    Payment_Date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    Payment_Method = db.Column(db.String(50), nullable=False, default="Credit Card")
    Payment_Status = db.Column(db.String(30), nullable=False, default=STATUS_COMPLETED)
    Transaction_Ref = db.Column(db.String(100), nullable=True)
    Payment_Purpose = db.Column(db.String(50), default="Booking Deposit") # Booking Deposit, Return Settlement, Damage/Late Fee
    
    # Relationships
    booking = db.relationship("Booking", back_populates="payments")
    rental = db.relationship("Rental", back_populates="payments")
    
    def to_dict(self) -> dict:
        return {
            "Payment_ID": self.Payment_ID,
            "Booking_ID": self.Booking_ID,
            "Rental_ID": self.Rental_ID,
            "Amount": self.Amount,
            "Payment_Date": self.Payment_Date.strftime("%Y-%m-%d %H:%M") if self.Payment_Date else None,
            "Payment_Method": self.Payment_Method,
            "Payment_Status": self.Payment_Status,
            "Payment_Purpose": self.Payment_Purpose,
            "Transaction_Ref": self.Transaction_Ref
        }
