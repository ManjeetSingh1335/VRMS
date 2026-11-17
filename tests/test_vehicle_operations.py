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
    InvalidStateTransitionError,
    InvalidDurationError,
    PaymentFailedError
)
from app.services.payment_gateway import PaymentGateway

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    GREEN_CACHE_TTL_SECONDS = 5

class TestVehicleOperations(unittest.TestCase):
    """Unit tests for vehicle state machine, rate calculations, and mock payment gateway."""
    
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Seed test vehicle 101
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

    def test_tc01_vehicle_availability(self):
        """TC-01: Check vehicle 101 availability initially returns Available=True."""
        vehicle = Vehicle.query.get(101)
        self.assertIsNotNone(vehicle, "Vehicle 101 should exist")
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_AVAILABLE)
        self.assertTrue(vehicle.Availability_Status == Vehicle.STATE_AVAILABLE)

    def test_tc02_reserve_vehicle(self):
        """TC-02: Reserve vehicle transitions Available -> Booked."""
        vehicle = Vehicle.query.get(101)
        vehicle.book_vehicle()
        db.session.commit()
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_BOOKED)

    def test_tc03_return_vehicle(self):
        """TC-03: Return vehicle transitions Rented -> Available."""
        vehicle = Vehicle.query.get(101)
        vehicle.book_vehicle()   # Available -> Booked
        vehicle.pickup_vehicle() # Booked -> Rented
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_RENTED)
        
        vehicle.return_vehicle() # Rented -> Available
        db.session.commit()
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_AVAILABLE)

    def test_tc04_payment_positive_amount(self):
        """TC-04: Payment of 7500 -> success."""
        result = PaymentGateway.makePayment(7500.0, method="Credit Card")
        self.assertTrue(result["success"])
        self.assertEqual(result["amount"], 7500.0)
        self.assertTrue(result["transaction_ref"].startswith("TXN-"))

    def test_tc05_payment_zero_amount(self):
        """TC-05: Payment of 0 -> fail (raises PaymentFailedError)."""
        with self.assertRaises(PaymentFailedError):
            PaymentGateway.makePayment(0.0)

    def test_ecp_invalid_state_transitions(self):
        """ECP: Test invalid vehicle state transitions raise InvalidStateTransitionError."""
        vehicle = Vehicle.query.get(101)
        
        # Available cannot directly pickup
        with self.assertRaises(InvalidStateTransitionError):
            vehicle.pickup_vehicle()
            
        # Available cannot directly return
        with self.assertRaises(InvalidStateTransitionError):
            vehicle.return_vehicle()
            
        # Available cannot directly report damage
        with self.assertRaises(InvalidStateTransitionError):
            vehicle.report_damage()

        # Available -> Booked
        vehicle.book_vehicle()
        # Booked cannot retire directly
        with self.assertRaises(InvalidStateTransitionError):
            vehicle.retire_vehicle()

    def test_boundary_values_duration(self):
        """Boundary Value Analysis: 0 days, negative days, and 1 day."""
        vehicle = Vehicle.query.get(101)
        
        # 0 days boundary -> InvalidDurationError
        with self.assertRaises(InvalidDurationError):
            vehicle.calculateRent(0)
            
        # Negative days boundary -> InvalidDurationError
        with self.assertRaises(InvalidDurationError):
            vehicle.calculateRent(-1)
            
        # 1 day boundary -> Success (2500.0)
        rent_1_day = vehicle.calculateRent(1)
        self.assertEqual(rent_1_day, 2500.0)

    def test_damage_and_maintenance_lifecycle(self):
        """Test reporting damage and maintenance recovery."""
        vehicle = Vehicle.query.get(101)
        vehicle.book_vehicle()
        vehicle.pickup_vehicle()
        
        # Report damage: Rented -> Under Maintenance
        vehicle.report_damage()
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_UNDER_MAINTENANCE)
        
        # Complete maintenance: Under Maintenance -> Available
        vehicle.complete_maintenance()
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_AVAILABLE)

    def test_retire_vehicle(self):
        """Test retiring an available vehicle."""
        vehicle = Vehicle.query.get(101)
        vehicle.retire_vehicle()
        self.assertEqual(vehicle.Availability_Status, Vehicle.STATE_RETIRED)
        
        # Retired vehicle cannot be booked
        with self.assertRaises(InvalidStateTransitionError):
            vehicle.book_vehicle()

if __name__ == "__main__":
    unittest.main()
