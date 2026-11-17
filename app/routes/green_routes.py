from flask import Blueprint, jsonify
from ..services.green_cache import green_cache

green_bp = Blueprint("green", __name__)

@green_bp.route("/api/green-metrics", methods=["GET"])
def get_green_metrics():
    """Green Software metrics comparison endpoint."""
    metrics = green_cache.get_metrics()
    return jsonify({
        "success": True,
        "metrics": metrics,
        "description": "Green computing telemetry: TTL caching & query projection impact."
    })

@green_bp.route("/api/green-metrics/reset", methods=["POST"])
def reset_green_metrics():
    green_cache.invalidate()
    green_cache.metrics = {
        "db_reads": 0,
        "db_writes": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "bytes_transferred": 0,
        "conventional_db_reads_estimated": 0
    }
    return jsonify({"success": True, "message": "Green metrics reset successfully."})
