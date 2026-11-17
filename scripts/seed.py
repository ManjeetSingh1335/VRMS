import os
import sys

# Ensure application package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models.entities import db, Customer, Administrator, RentalStaff, Vehicle, Booking, Payment, Rental

def seed_database():
    app = create_app()
    with app.app_context():
        # Drop and create tables cleanly
        db.create_all()
        
        # Check if already seeded
        if Customer.query.count() > 0:
            print("Database already contains data. Skipping re-seed.")
            return

        print("Seeding VRMS Database with sample users and vehicles...")

        # 1. Administrator
        admin = Customer(
            Customer_Name="Rajesh Sharma (Admin)",
            Email="admin@vrms.com",
            Phone="+91-9811002233",
            Address="MAIT Campus, Rohini Sector 22, Delhi",
            License_Number="DL-ADMIN-2020",
            Role="Administrator"
        )
        admin.set_password("admin123")
        db.session.add(admin)

        # 2. Rental Staff
        staff = Customer(
            Customer_Name="Vikram Malhotra (Staff)",
            Email="staff@vrms.com",
            Phone="+91-9811004455",
            Address="Staff Quarters, Sector 22, Rohini, Delhi",
            License_Number="DL-STAFF-2021",
            Role="Rental Staff"
        )
        staff.set_password("staff123")
        db.session.add(staff)

        # 3. Customer 1 (Aarav Mehta - Target ID 201 if possible)
        customer1 = Customer(
            Customer_ID=201,
            Customer_Name="Aarav Mehta",
            Email="aarav@gmail.com",
            Phone="+91-9876543210",
            Address="Flat 402, Sunshine Heights, Dwarka Sector 10, Delhi",
            License_Number="DL-04-2022-0091",
            Role="Customer"
        )
        customer1.set_password("cust123")
        db.session.add(customer1)

        # 4. Customer 2 (Priya Sharma)
        customer2 = Customer(
            Customer_ID=202,
            Customer_Name="Priya Sharma",
            Email="priya@gmail.com",
            Phone="+91-9812345678",
            Address="B-12, Model Town, Delhi",
            License_Number="DL-12-2021-4820",
            Role="Customer"
        )
        customer2.set_password("cust123")
        db.session.add(customer2)

        # 5. 10 Fleet Vehicles (Vehicle 101 Honda City with Rate 2500.0)
        vehicles_data = [
            {
                "Vehicle_ID": 101,
                "Registration_Number": "DL-01-AB-1001",
                "Model": "Honda City 1.5 i-VTEC",
                "Vehicle_Type": "Sedan",
                "Rental_Rate": 2500.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 15400.0,
                "Image_URL": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=600&auto=format&fit=crop&q=80",
                "Features": "Automatic, Sunroof, Apple CarPlay, 5 Seater, Cruise Control"
            },
            {
                "Vehicle_ID": 102,
                "Registration_Number": "DL-01-CD-1002",
                "Model": "Hyundai Creta SX(O)",
                "Vehicle_Type": "SUV",
                "Rental_Rate": 3200.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 22100.0,
                "Image_URL": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=600&auto=format&fit=crop&q=80",
                "Features": "Panoramic Sunroof, Ventilated Seats, ADAS, 5 Seater"
            },
            {
                "Vehicle_ID": 103,
                "Registration_Number": "DL-03-EF-1003",
                "Model": "Maruti Swift ZXi+",
                "Vehicle_Type": "Hatchback",
                "Rental_Rate": 1600.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 31050.0,
                "Image_URL": "https://images.unsplash.com/photo-1502877338535-766e1452684a?w=600&auto=format&fit=crop&q=80",
                "Features": "Manual, High Fuel Efficiency, AC, Touchscreen"
            },
            {
                "Vehicle_ID": 104,
                "Registration_Number": "DL-04-GH-1004",
                "Model": "Toyota Fortuner 4x4",
                "Vehicle_Type": "SUV",
                "Rental_Rate": 5500.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 45000.0,
                "Image_URL": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?w=600&auto=format&fit=crop&q=80",
                "Features": "4WD, 7 Seater, Leather Upholstery, Hill Assist"
            },
            {
                "Vehicle_ID": 105,
                "Registration_Number": "DL-05-IJ-1005",
                "Model": "BMW 3 Series Gran Limousine",
                "Vehicle_Type": "Luxury",
                "Rental_Rate": 8500.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 12000.0,
                "Image_URL": "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=600&auto=format&fit=crop&q=80",
                "Features": "Executive Lounge, Harman Kardon Audio, Twin Turbo"
            },
            {
                "Vehicle_ID": 106,
                "Registration_Number": "DL-06-KL-1006",
                "Model": "Tata Nexon EV Max",
                "Vehicle_Type": "SUV",
                "Rental_Rate": 2800.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 18200.0,
                "Image_URL": "https://images.unsplash.com/photo-1563720223185-11003d516935?w=600&auto=format&fit=crop&q=80",
                "Features": "100% Electric, 400km Range, Fast Charging, Zero Emission"
            },
            {
                "Vehicle_ID": 107,
                "Registration_Number": "DL-07-MN-1007",
                "Model": "Mahindra Thar 4x4 Hardtop",
                "Vehicle_Type": "SUV",
                "Rental_Rate": 3800.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 27400.0,
                "Image_URL": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=600&auto=format&fit=crop&q=80",
                "Features": "Offroad Specialist, Convertible Roof, 4 Seater"
            },
            {
                "Vehicle_ID": 108,
                "Registration_Number": "DL-08-OP-1008",
                "Model": "Mercedes-Benz E-Class",
                "Vehicle_Type": "Luxury",
                "Rental_Rate": 9800.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 9500.0,
                "Image_URL": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=600&auto=format&fit=crop&q=80",
                "Features": "Chauffeur Comfort, Burmester 3D Sound, Ambient Lighting"
            },
            {
                "Vehicle_ID": 109,
                "Registration_Number": "DL-09-QR-1009",
                "Model": "Isuzu D-Max V-Cross",
                "Vehicle_Type": "Truck",
                "Rental_Rate": 4200.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 38900.0,
                "Image_URL": "https://images.unsplash.com/photo-1559416523-140ddc3d238c?w=600&auto=format&fit=crop&q=80",
                "Features": "Pickup Truck, Huge Cargo Deck, 4x4 Shift-on-the-fly"
            },
            {
                "Vehicle_ID": 110,
                "Registration_Number": "DL-10-ST-1010",
                "Model": "Kia Carnival Limousine",
                "Vehicle_Type": "Luxury",
                "Rental_Rate": 6000.0,
                "Availability_Status": Vehicle.STATE_AVAILABLE,
                "Current_Odometer": 19400.0,
                "Image_URL": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=600&auto=format&fit=crop&q=80",
                "Features": "VIP Reclining Seats, Dual Entertainment Screens, 7 Seater"
            }
        ]

        for v_data in vehicles_data:
            veh = Vehicle(**v_data)
            db.session.add(veh)

        db.session.commit()
        print("Successfully seeded 4 users and 10 vehicles!")

if __name__ == "__main__":
    seed_database()
