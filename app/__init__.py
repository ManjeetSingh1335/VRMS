from flask import Flask, jsonify
from .config import Config
from .models.entities import db
from .services.green_cache import green_cache

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    app.config.from_object(config_class)
    
    # Initialize database
    db.init_app(app)
    
    # Register Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.customer_routes import customer_bp
    from .routes.admin_routes import admin_bp
    from .routes.staff_routes import staff_bp
    from .routes.green_routes import green_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(green_bp)
    
    # Track transfer bytes in after_request for Green Software metrics
    @app.after_request
    def record_metrics_after_request(response):
        try:
            content_length = response.calculate_content_length()
            if content_length:
                green_cache.record_transfer(content_length)
        except Exception:
            pass
        return response

    # Global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"success": False, "error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app
