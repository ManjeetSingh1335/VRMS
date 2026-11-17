from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import func
from ..models.entities import db, Vehicle, Customer, Booking, Rental, Payment
from ..models.exceptions import VRMSError
from ..services.vehicle_db import VehicleDB
from ..utils.auth import login_required, role_required, get_current_user

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
@login_required
@role_required(["Administrator"])
def admin_dashboard():
    user = get_current_user()
    return render_template("admin_dashboard.html", user=user)

@admin_bp.route("/api/admin/vehicles", methods=["GET", "POST"])
@login_required
@role_required(["Administrator"])
def manage_vehicles():
    if request.method == "POST":
        data = request.get_json() or {}
        try:
            vehicle = VehicleDB.addVehicle(
                registration_number=data.get("registration_number"),
                model=data.get("model"),
                vehicle_type=data.get("vehicle_type"),
                rental_rate=float(data.get("rental_rate")),
                current_odometer=float(data.get("current_odometer", 0.0)),
                image_url=data.get("image_url"),
                features=data.get("features")
            )
            return jsonify({"success": True, "message": "Vehicle added successfully", "vehicle": vehicle.to_dict(full=True)}), 201
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
            
    # GET list
    vehicles = Vehicle.query.order_by(Vehicle.Vehicle_ID.asc()).all()
    return jsonify({"success": True, "vehicles": [v.to_dict(full=True) for v in vehicles]})

@admin_bp.route("/api/admin/vehicles/<int:vehicle_id>", methods=["PUT", "DELETE"])
@login_required
@role_required(["Administrator"])
def edit_vehicle(vehicle_id: int):
    if request.method == "DELETE":
        try:
            vehicle = VehicleDB.deactivateVehicle(vehicle_id)
            return jsonify({"success": True, "message": f"Vehicle {vehicle.Registration_Number} deactivated/retired successfully", "vehicle": vehicle.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
            
    data = request.get_json() or {}
    try:
        vehicle = VehicleDB.updateVehicle(
            vehicle_id=vehicle_id,
            model=data.get("model"),
            vehicle_type=data.get("vehicle_type"),
            rental_rate=float(data["rental_rate"]) if "rental_rate" in data else None,
            availability_status=data.get("availability_status"),
            current_odometer=float(data["current_odometer"]) if "current_odometer" in data else None,
            features=data.get("features")
        )
        return jsonify({"success": True, "message": "Vehicle updated successfully", "vehicle": vehicle.to_dict(full=True)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@admin_bp.route("/api/admin/customers", methods=["GET"])
@login_required
@role_required(["Administrator"])
def list_customers():
    customers = Customer.query.order_by(Customer.Created_At.desc()).all()
    return jsonify({"success": True, "customers": [c.to_dict() for c in customers]})

@admin_bp.route("/api/admin/bookings", methods=["GET"])
@login_required
@role_required(["Administrator"])
def list_all_bookings():
    bookings = Booking.query.order_by(Booking.Booking_Date.desc()).all()
    return jsonify({"success": True, "bookings": [b.to_dict() for b in bookings]})

@admin_bp.route("/api/admin/payments", methods=["GET"])
@login_required
@role_required(["Administrator"])
def list_all_payments():
    payments = Payment.query.order_by(Payment.Payment_Date.desc()).all()
    return jsonify({"success": True, "payments": [p.to_dict() for p in payments]})

@admin_bp.route("/api/admin/reports", methods=["GET"])
@login_required
@role_required(["Administrator"])
def get_reports():
    """Generate business intelligence analytics: revenue, bookings, fleet status, and vehicle utilization."""
    total_vehicles = Vehicle.query.count()
    total_customers = Customer.query.filter_by(Role="Customer").count()
    total_bookings = Booking.query.count()
    
    # Revenue calculations
    total_revenue = db.session.query(func.coalesce(func.sum(Payment.Amount), 0.0)).filter(
        Payment.Payment_Status == Payment.STATUS_COMPLETED
    ).scalar()
    
    # Vehicle status distribution
    status_counts = db.session.query(
        Vehicle.Availability_Status, func.count(Vehicle.Vehicle_ID)
    ).group_by(Vehicle.Availability_Status).all()
    status_dict = {status: count for status, count in status_counts}
    for s in Vehicle.VALID_STATES:
        status_dict.setdefault(s, 0)
        
    # Fleet utilization percentage: (Rented + Booked) / Total * 100
    active_in_use = status_dict.get(Vehicle.STATE_RENTED, 0) + status_dict.get(Vehicle.STATE_BOOKED, 0)
    utilization_rate = round((active_in_use / total_vehicles * 100), 1) if total_vehicles > 0 else 0.0
    
    # Monthly/Recent revenue trends (last 6 months or recent payments)
    revenue_by_method = db.session.query(
        Payment.Payment_Method, func.sum(Payment.Amount)
    ).filter(Payment.Payment_Status == Payment.STATUS_COMPLETED).group_by(Payment.Payment_Method).all()
    
    # Vehicle bookings frequency
    top_vehicles = db.session.query(
        Vehicle.Model, func.count(Booking.Booking_ID)
    ).join(Booking, Vehicle.Vehicle_ID == Booking.Vehicle_ID).group_by(Vehicle.Model).order_by(
        func.count(Booking.Booking_ID).desc()
    ).limit(5).all()

    return jsonify({
        "success": True,
        "kpis": {
            "total_vehicles": total_vehicles,
            "total_customers": total_customers,
            "total_bookings": total_bookings,
            "total_revenue": round(float(total_revenue), 2),
            "utilization_rate": utilization_rate
        },
        "status_distribution": status_dict,
        "revenue_by_method": {method: round(float(amt), 2) for method, amt in revenue_by_method},
        "top_vehicles": [{"model": model, "bookings_count": count} for model, count in top_vehicles]
    })
