from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from ..models.entities import Customer

def get_current_user():
    """Retrieve logged in customer/admin/staff from session."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return Customer.query.get(user_id)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required", "success": False}), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """Decorator ensuring current user has one of allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required", "success": False}), 401
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login_page"))
                
            user_role = session.get("user_role")
            if user_role not in roles:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Unauthorized access for your role", "success": False}), 403
                flash("Access denied: You do not have permission for this section.", "danger")
                return redirect(url_for("auth.dashboard_redirect"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
