import os
import sys
from app import create_app
from app.models.entities import db, Vehicle
from scripts.seed import seed_database

app = create_app()

def initialize_app():
    with app.app_context():
        db.create_all()
        # Auto seed if fleet is empty
        if Vehicle.query.count() == 0:
            print("[INFO] Vehicle fleet empty. Auto-seeding initial database...")
            seed_database()

if __name__ == "__main__":
    initialize_app()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================================")
    print(f"  Vehicle Rental Management System (VRMS) Started Successfully!  ")
    print(f"  Access web application at: http://127.0.0.1:{port}             ")
    print(f"==================================================================\n")
    app.run(host="0.0.0.0", port=port, debug=True)
