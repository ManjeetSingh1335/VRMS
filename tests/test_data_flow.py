import unittest
from datetime import datetime, date, timedelta
import os
import sys

# Ensure application package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config import Config
from app.models.entities import db, Vehicle, Customer, Booking, Payment
from app.models.exceptions import (
    VehicleNotFoundError,
    VehicleUnavailableError,
    InvalidDurationError,
    PaymentFailedError
)
from app.services.booking_service import BookingService
from app.services.vehicle_db import VehicleDB

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class TestDataFlow(unittest.TestCase):
    """Data-flow test suite (DF-01 through DF-06) testing DU-chains in the booking pipeline."""

    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Seed Customer 201
        self.cust201 = Customer(
            Customer_ID=201,
            Customer_Name="Aarav Mehta",
            Email="aarav@gmail.com",
            Phone="+91-9876543210",
            Address="Dwarka Sector 10, Delhi",
            License_Number="DL-04-2022-0091",
            Role="Customer"
        )
        self.cust201.set_password("cust123")
        db.session.add(self.cust201)

        # Seed Vehicle 101 with daily rate 2500
        self.v101 = Vehicle(
            Vehicle_ID=101,
            Registration_Number="DL-01-AB-1001",
            Model="Honda City 1.5 i-VTEC",
            Vehicle_Type="Sedan",
            Rental_Rate=2500.0,
            Availability_Status=Vehicle.STATE_AVAILABLE,
            Current_Odometer=15000.0
        )
        db.session.add(self.v101)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_df01_valid_booking(self):
        """DF-01: Valid booking path with Vehicle 101 for 3 days."""
        pickup = date.today() + timedelta(days=2)
        return_d = pickup + timedelta(days=3)
        
        booking = BookingService.bookVehicle(
            customer_id=201,
            vehicle_id=101,
            pickup_date=pickup,
            return_date=return_d
        )
        
        self.assertIsNotNone(booking.Booking_ID)
        self.assertEqual(booking.Vehicle_ID, 101)
        self.assertEqual(booking.Customer_ID, 201)
        self.assertEqual(booking.Booking_Status, Booking.STATUS_CONFIRMED)

    def test_df02_vehicle_unavailable(self):
        """DF-02: Path where vehicle is unavailable due to overlapping active booking."""
        pickup = date.today() + timedelta(days=5)
        return_d = pickup + timedelta(days=3)
        
        # Initial booking occupying timeframe
        BookingService.bookVehicle(
            customer_id=201,
            vehicle_id=101,
            pickup_date=pickup,
            return_date=return_d
        )
        
        # Overlapping booking attempt on same vehicle
        with self.assertRaises(VehicleUnavailableError) as ctx:
            BookingService.bookVehicle(
                customer_id=201,
                vehicle_id=101,
                pickup_date=pickup + timedelta(days=1),
                return_date=return_d + timedelta(days=2)
            )
        self.assertIn("not available", str(ctx.exception))

    def test_df03_days_zero_invalid_duration(self):
        """DF-03: Path where days = 0 or return_date <= pickup_date raises InvalidDurationError."""
        same_day = date.today() + timedelta(days=1)
        
        with self.assertRaises(InvalidDurationError):
            BookingService.bookVehicle(
                customer_id=201,
                vehicle_id=101,
                pickup_date=same_day,
                return_date=same_day # 0 days
            )

    def test_df04_payment_failure(self):
        """DF-04: Path where payment gateway fails or amount <= 0."""
        pickup = date.today() + timedelta(days=15)
        return_d = pickup + timedelta(days=2)
        
        with self.assertRaises(PaymentFailedError):
            BookingService.bookVehicle(
                customer_id=201,
                vehicle_id=101,
                pickup_date=pickup,
                return_date=return_d,
                simulate_payment_failure=True
            )

    def test_df05_vehicle_not_found(self):
        """DF-05: Path where vehicle ID does not exist (ID 999 not found)."""
        pickup = date.today() + timedelta(days=1)
        return_d = pickup + timedelta(days=2)
        
        with self.assertRaises(VehicleNotFoundError) as ctx:
            BookingService.bookVehicle(
                customer_id=201,
                vehicle_id=999, # Non-existent ID
                pickup_date=pickup,
                return_date=return_d
            )
        self.assertIn("Vehicle not found", str(ctx.exception))

    def test_df06_rate_multiplication_calculation(self):
        """DF-06: Calculation path: Rate 2500 x 3 days = 7500."""
        daily_rate = 2500.0
        days = 3
        total = BookingService.calculateRent(daily_rate, days)
        self.assertEqual(total, 7500.0)

        # Verify through full booking flow
        pickup = date.today() + timedelta(days=20)
        return_d = pickup + timedelta(days=3)
        booking = BookingService.bookVehicle(
            customer_id=201,
            vehicle_id=101,
            pickup_date=pickup,
            return_date=return_d
        )
        self.assertEqual(booking.Total_Amount, 7500.0)

if __name__ == "__main__":
    unittest.main()
