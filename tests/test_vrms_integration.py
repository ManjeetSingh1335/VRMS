import unittest
from datetime import datetime, date, timedelta
import os
import sys

# Ensure application package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.config import Config
from app.models.entities import db, Vehicle, Customer, Booking, Payment, Rental
from app.models.exceptions import (
    VehicleUnavailableError,
    PaymentFailedError,
    InvalidDurationError
)
from app.services.booking_service import BookingService
from app.services.vehicle_db import VehicleDB

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class TestVRMSIntegration(unittest.TestCase):
    """Integration test suite for end-to-end booking, payment rollback, and overlap prevention."""

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

        # Seed Vehicle 101
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

    def test_tc06_customer_201_vehicle_101_3_days_booking_501(self):
        """TC-06: Customer 201 books Vehicle 101 for 3 days -> Booking ID 501 created."""
        pickup = date.today() + timedelta(days=1)
        return_d = pickup + timedelta(days=3)
        
        booking = BookingService.bookVehicle(
            customer_id=201,
            vehicle_id=101,
            pickup_date=pickup,
            return_date=return_d,
            payment_method="Credit Card",
            custom_booking_id=501
        )
        
        self.assertIsNotNone(booking)
        self.assertEqual(booking.Booking_ID, 501)
        self.assertEqual(booking.Customer_ID, 201)
        self.assertEqual(booking.Vehicle_ID, 101)
        self.assertEqual(booking.Total_Amount, 7500.0) # 2500 * 3
        self.assertEqual(booking.Booking_Status, Booking.STATUS_CONFIRMED)
        
        # Verify Vehicle status updated to Booked
        vehicle = Vehicle.query.get(101)
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_BOOKED)
        
        # Verify payment recorded
        self.assertEqual(len(booking.payments), 1)
        self.assertEqual(booking.payments[0].Amount, 7500.0)
        self.assertEqual(booking.payments[0].Payment_Status, Payment.STATUS_COMPLETED)

    def test_tc07_payment_failure_booking_not_created(self):
        """TC-07: Payment failure -> booking is NOT created (atomic transaction rollback)."""
        pickup = date.today() + timedelta(days=5)
        return_d = pickup + timedelta(days=2)
        initial_bookings_count = Booking.query.count()
        
        with self.assertRaises(PaymentFailedError):
            BookingService.bookVehicle(
                customer_id=201,
                vehicle_id=101,
                pickup_date=pickup,
                return_date=return_d,
                payment_method="Credit Card",
                simulate_payment_failure=True # Force simulated payment decline
            )
            
        # Verify no booking created
        self.assertEqual(Booking.query.count(), initial_bookings_count)
        
        # Verify vehicle remains Available
        vehicle = Vehicle.query.get(101)
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_AVAILABLE)

    def test_tc08_book_already_booked_vehicle_rejected(self):
        """TC-08: Attempting to book an already-booked vehicle during overlapping period is rejected."""
        pickup = date.today() + timedelta(days=10)
        return_d = pickup + timedelta(days=3)
        
        # Initial successful booking
        BookingService.bookVehicle(
            customer_id=201,
            vehicle_id=101,
            pickup_date=pickup,
            return_date=return_d,
            payment_method="Credit Card"
        )
        
        # Second customer attempts to book same vehicle in overlapping interval
        with self.assertRaises(VehicleUnavailableError):
            BookingService.bookVehicle(
                customer_id=201,
                vehicle_id=101,
                pickup_date=pickup + timedelta(days=1),
                return_date=return_d + timedelta(days=1)
            )

    def test_full_rental_lifecycle_with_return_receipt(self):
        """Test full workflow: Book -> Pickup -> Return with late fee & generate receipt."""
        pickup = date.today()
        return_d = pickup + timedelta(days=2)
        
        # 1. Book
        booking = BookingService.bookVehicle(
            customer_id=201,
            vehicle_id=101,
            pickup_date=pickup,
            return_date=return_d
        )
        self.assertEqual(booking.Booking_Status, Booking.STATUS_CONFIRMED)
        
        # 2. Pickup
        rental = BookingService.pickupVehicle(
            booking_id=booking.Booking_ID,
            start_odometer=15000.0
        )
        self.assertEqual(rental.booking.Booking_Status, Booking.STATUS_ACTIVE)
        self.assertEqual(rental.booking.vehicle.Availability_Status, Vehicle.STATE_RENTED)
        
        # 3. Return 1 day late with 500 damage fee
        simulated_return_time = datetime.combine(return_d + timedelta(days=1), datetime.min.time()) + timedelta(hours=14)
        receipt = BookingService.returnVehicle(
            booking_id=booking.Booking_ID,
            end_odometer=15350.0,
            damage_fee=500.0,
            damage_notes="Scratch on left bumper",
            actual_return_date=simulated_return_time
        )
        
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["booking_id"], booking.Booking_ID)
        self.assertEqual(receipt["rental_period"]["late_days"], 1)
        self.assertEqual(receipt["vehicle"]["status"], Vehicle.STATE_UNDER_MAINTENANCE) # Damaged -> Under Maintenance
        self.assertEqual(receipt["odometer"]["distance_traveled"], 350.0)
        self.assertTrue(receipt["financial_breakdown"]["total_paid"] > 5000.0)

if __name__ == "__main__":
    unittest.main()
