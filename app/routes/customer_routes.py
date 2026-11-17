from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
from ..models.entities import db, Vehicle, Booking
from ..models.exceptions import VRMSError
from ..services.vehicle_db import VehicleDB
from ..services.booking_service import BookingService
from ..utils.auth import login_required, role_required, get_current_user

customer_bp = Blueprint("customer", __name__)

@customer_bp.route("/customer/dashboard")
@login_required
@role_required(["Customer", "Administrator"])
def customer_dashboard():
    user = get_current_user()
    return render_template("customer_dashboard.html", user=user)

@customer_bp.route("/api/vehicles/search", methods=["GET"])
def search_vehicles_api():
    """Green Software search API: pagination + selective field projection."""
    pickup_str = request.args.get("pickup_date")
    return_str = request.args.get("return_date")
    vehicle_type = request.args.get("type", "All")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 8))
    
    pickup_date = None
    return_date = None
    if pickup_str and return_str:
        try:
            pickup_date = datetime.strptime(pickup_str, "%Y-%m-%d").date()
            return_date = datetime.strptime(return_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
    result = VehicleDB.searchAvailableVehicles(
        pickup_date=pickup_date,
        return_date=return_date,
        vehicle_type=vehicle_type,
        page=page,
        page_size=page_size,
        projection_only=True
    )
    return jsonify({"success": True, **result})

@customer_bp.route("/api/vehicles/<int:vehicle_id>", methods=["GET"])
def get_vehicle_details(vehicle_id: int):
    try:
        vehicle = VehicleDB.getVehicle(vehicle_id, use_cache=True)
        return jsonify({"success": True, "vehicle": vehicle.to_dict(full=True)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 404

@customer_bp.route("/api/bookings/preview", methods=["POST"])
def preview_booking():
    data = request.get_json() or {}
    try:
        vehicle_id = int(data.get("vehicle_id"))
        pickup_date = datetime.strptime(data.get("pickup_date"), "%Y-%m-%d").date()
        return_date = datetime.strptime(data.get("return_date"), "%Y-%m-%d").date()
        
        vehicle = VehicleDB.getVehicle(vehicle_id)
        if return_date <= pickup_date:
            return jsonify({"success": False, "error": "Return date must be after pickup date"}), 400
            
        days = (return_date - pickup_date).days
        total_rent = BookingService.calculateRent(vehicle.Rental_Rate, days)
        available = VehicleDB.isVehicleAvailable(vehicle_id, pickup_date, return_date)
        
        return jsonify({
            "success": True,
            "vehicle_id": vehicle.Vehicle_ID,
            "model": vehicle.Model,
            "daily_rate": vehicle.Rental_Rate,
            "duration_days": days,
            "total_rent": total_rent,
            "is_available": available
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@customer_bp.route("/api/bookings/create", methods=["POST"])
@login_required
def create_booking_api():
    user = get_current_user()
    data = request.get_json() or {}
    
    try:
        vehicle_id = int(data.get("vehicle_id"))
        pickup_date = datetime.strptime(data.get("pickup_date"), "%Y-%m-%d").date()
        return_date = datetime.strptime(data.get("return_date"), "%Y-%m-%d").date()
        payment_method = data.get("payment_method", "Credit Card")
        simulate_failure = bool(data.get("simulate_payment_failure", False))
        
        booking = BookingService.bookVehicle(
            customer_id=user.Customer_ID,
            vehicle_id=vehicle_id,
            pickup_date=pickup_date,
            return_date=return_date,
            payment_method=payment_method,
            simulate_payment_failure=simulate_failure
        )
        
        return jsonify({
            "success": True,
            "message": "Booking confirmed and payment processed successfully!",
            "booking": booking.to_dict()
        }), 201
        
    except VRMSError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal booking error: {str(e)}"}), 500

@customer_bp.route("/api/bookings/my", methods=["GET"])
@login_required
def get_my_bookings():
    user = get_current_user()
    bookings = Booking.query.filter_by(Customer_ID=user.Customer_ID).order_by(Booking.Booking_Date.desc()).all()
    return jsonify({
        "success": True,
        "bookings": [b.to_dict() for b in bookings]
    })

@customer_bp.route("/api/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking_api(booking_id: int):
    user = get_current_user()
    try:
        booking = BookingService.cancelBooking(booking_id=booking_id, customer_id=user.Customer_ID)
        return jsonify({
            "success": True,
            "message": f"Booking #{booking_id} cancelled successfully. Cancellation fee: ₹{booking.Cancellation_Fee:.2f}",
            "booking": booking.to_dict()
        })
    except VRMSError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
