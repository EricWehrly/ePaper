"""
Flask web server for ePaper display control

Provides a lightweight web interface for controlling the ePaper display,
including image upload, conversion, and display management.
"""

import logging
from flask import Flask
from .routes import register_routes

logger = logging.getLogger(__name__)

def create_app(epaper_controller=None):
    """
    Create and configure the Flask application
    
    Args:
        epaper_controller: Instance of ePaperController for display operations
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Store controller reference for routes to access
    app.epaper_controller = epaper_controller
    
    # Register API routes
    register_routes(app)
    
    # Basic error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Endpoint not found"}, 404
        
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {"error": "Internal server error"}, 500
    
    return app

def start_server(epaper_controller=None, host='0.0.0.0', port=5000, debug=False):
    """
    Start the Flask web server
    
    Args:
        epaper_controller: Instance of ePaperController for display operations
        host: Host address to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to listen on (default: 5000)
        debug: Enable Flask debug mode (default: False)
    """
    app = create_app(epaper_controller)
    
    logger.info(f"Starting ePaper web server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)