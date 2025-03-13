from flask import jsonify, current_app

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        current_app.logger.error(f"API Error: {error.message} (Status: {error.status_code})")
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors"""
        current_app.logger.error(f"Bad Request: {error}")
        return jsonify({"error": "Bad request"}), 400
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors"""
        current_app.logger.error(f"Not Found: {error}")
        return jsonify({"error": "Resource not found"}), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle method not allowed errors"""
        current_app.logger.error(f"Method Not Allowed: {error}")
        return jsonify({"error": "Method not allowed"}), 405
    
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle internal server errors"""
        current_app.logger.error(f"Internal Server Error: {error}")
        return jsonify({"error": "Internal server error"}), 500
    
    return app 