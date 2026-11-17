from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from ..models.entities import Booking, Rental, Vehicle
from ..models.exceptions import VRMSError
from ..services.booking_service import BookingService
from ..utils.auth import login_required, role_required, get_current_user

staff_bp = Blueprint("staff", __name__)

@staff_bp.route("/staff/panel")
@login_required
@role_required(["Rental Staff", "Administrator"])
def staff_panel():
    user = get_current_user()
    return render_template("staff_panel.html", user=user)

@staff_bp.route("/api/staff/booking/<int:booking_id>", methods=["GET"])
@login_required
@role_required(["Rental Staff", "Administrator"])
def lookup_booking(booking_id: int):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"success": False, "error": f"Booking ID {booking_id} not found."}), 404
        
    rental_data = booking.rental.to_dict() if booking.rental else None
    return jsonify({
        "success": True,
        "booking": booking.to_dict(),
        "rental": rental_data
    })

@staff_bp.route("/api/staff/pickup", methods=["POST"])
@login_required
@role_required(["Rental Staff", "Administrator"])
def process_pickup():
    user = get_current_user()
    data = request.get_json() or {}
    try:
        booking_id = int(data.get("booking_id"))
        start_odometer = float(data["start_odometer"]) if "start_odometer" in data and data["start_odometer"] is not None else None
        
        rental = BookingService.pickupVehicle(
            booking_id=booking_id,
            staff_id=user.Customer_ID,
            start_odometer=start_odometer
        )
        return jsonify({
            "success": True,
            "message": f"Vehicle successfully handed over to customer. Rental ID: {rental.Rental_ID}",
            "rental": rental.to_dict()
        })
    except VRMSError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@staff_bp.route("/api/staff/return", methods=["POST"])
@login_required
@role_required(["Rental Staff", "Administrator"])
def process_return():
    """UC-08 Return Vehicle Flow Implementation."""
    user = get_current_user()
    data = request.get_json() or {}
    try:
        booking_id = int(data.get("booking_id"))
        end_odometer = float(data.get("end_odometer"))
        damage_fee = float(data.get("damage_fee", 0.0))
        damage_notes = data.get("damage_notes")
        payment_method = data.get("payment_method", "Credit Card")
        simulate_failure = bool(data.get("simulate_payment_failure", False))
        
        actual_return_date = None
        if data.get("actual_return_date"):
            actual_return_date = datetime.strptime(data.get("actual_return_date"), "%Y-%m-%d %H:%M")
            
        receipt = BookingService.returnVehicle(
            booking_id=booking_id,
            staff_id=user.Customer_ID,
            end_odometer=end_odometer,
            damage_fee=damage_fee,
            damage_notes=damage_notes,
            actual_return_date=actual_return_date,
            payment_method=payment_method,
            simulate_payment_failure=simulate_failure
        )
        
        return jsonify({
            "success": True,
            "message": "Vehicle returned and processed successfully! Return receipt generated.",
            "receipt": receipt
        })
    except VRMSError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@staff_bp.route("/receipt/<int:booking_id>")
@login_required
def view_receipt(booking_id: int):
    booking = Booking.query.get_or_404(booking_id)
    if not booking.rental:
        return "No rental record available for this booking.", 404
        
    return render_template("receipt.html", booking=booking, rental=booking.rental)
