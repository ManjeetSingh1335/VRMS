from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from ..models.entities import db, Customer
from ..utils.auth import login_required, get_current_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard_redirect"))
    return render_template("index.html")

@auth_bp.route("/dashboard")
def dashboard_redirect():
    role = session.get("user_role")
    if role == "Administrator":
        return redirect(url_for("admin.admin_dashboard"))
    elif role == "Rental Staff":
        return redirect(url_for("staff.staff_panel"))
    else:
        return redirect(url_for("customer.customer_dashboard"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        user = Customer.query.filter_by(Email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.Customer_ID
            session["user_name"] = user.Customer_Name
            session["user_email"] = user.Email
            session["user_role"] = user.Role
            flash(f"Welcome back, {user.Customer_Name}!", "success")
            
            next_page = request.args.get("next")
            if next_page and not next_page.startswith("/api/"):
                return redirect(next_page)
            return redirect(url_for("auth.dashboard_redirect"))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        license_number = request.form.get("license_number", "").strip().upper()
        password = request.form.get("password", "")
        role = request.form.get("role", "Customer").strip()
        
        if not all([name, email, phone, address, license_number, password]):
            flash("All fields are required.", "warning")
            return render_template("register.html")
            
        if Customer.query.filter_by(Email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")
            
        # Role safety: only allow Customer registration from public form unless explicitly configured
        if role not in ["Customer", "Rental Staff", "Administrator"]:
            role = "Customer"
            
        new_customer = Customer(
            Customer_Name=name,
            Email=email,
            Phone=phone,
            Address=address,
            License_Number=license_number,
            Role=role
        )
        new_customer.set_password(password)
        db.session.add(new_customer)
        db.session.commit()
        
        flash("Registration successful! You may now log in.", "success")
        return redirect(url_for("auth.login_page"))
        
    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been safely logged out.", "info")
    return redirect(url_for("auth.index"))

@auth_bp.route("/api/auth/me")
@login_required
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    return jsonify({"success": True, "user": user.to_dict()})

@auth_bp.route("/api/auth/profile", methods=["PUT", "POST"])
@login_required
def update_profile():
    user = get_current_user()
    data = request.get_json() or request.form
    
    if "name" in data:
        user.Customer_Name = data["name"].strip()
    if "phone" in data:
        user.Phone = data["phone"].strip()
    if "address" in data:
        user.Address = data["address"].strip()
    if "license_number" in data:
        user.License_Number = data["license_number"].strip().upper()
        
    db.session.commit()
    return jsonify({"success": True, "message": "Profile updated successfully", "user": user.to_dict()})
