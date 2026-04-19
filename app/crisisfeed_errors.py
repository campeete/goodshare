from flask import jsonify
from app.crisisfeed_logger import get_logger

logger = get_logger(__name__)

def error_response(message, code, status):
    logger.warning(f"Error: {status} | {code} | {message}")
    return jsonify({"error": message, "code": code, "status": status}), status

def success_response(data, status=200):
    return jsonify(data), status

def not_found(resource):
    return error_response(f"{resource} not found", "NOT_FOUND", 404)

def bad_request(detail):
    return error_response(detail, "BAD_REQUEST", 400)

def validation_error(field, detail):
    return error_response(f"Validation error on '{field}': {detail}", "VALIDATION_ERROR", 422)

def service_unavailable(service):
    return error_response(f"{service}", "SERVICE_UNAVAILABLE", 503)

def internal_error(detail="An unexpected error occurred"):
    return error_response(detail, "INTERNAL_ERROR", 500)

def register_error_handlers(app):
    @app.errorhandler(404)
    def handle_404(e):
        return not_found("Endpoint")
    @app.errorhandler(500)
    def handle_500(e):
        logger.error(f"Unhandled 500: {e}", exc_info=True)
        return internal_error()
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {type(e).__name__}: {e}", exc_info=True)
        return internal_error()
