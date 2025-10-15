"""
Flask web server for ePaper display control

Provides a lightweight web interface for controlling the ePaper display,
including image upload, conversion, and display management.
"""

import logging
from flask import Flask, send_file, request, abort, send_from_directory
from werkzeug.serving import make_server
from .routes import register_routes
from pathlib import Path

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

    # Resolve static directory (module-relative) to avoid depending on CWD
    module_dir = Path(__file__).resolve().parent
    static_dir = module_dir / 'static'

    # Serve the single-page UI at /
    @app.route('/')
    def index():
        index_path = static_dir / 'index.html'
        if not index_path.exists():
            abort(404)
        return send_from_directory(str(static_dir), 'index.html')

    # Serve static assets (css/js) — Flask's static folder is not used to keep repo layout simple
    @app.route('/static/<path:filename>')
    def static_files(filename):
        file_path = static_dir / filename
        if not file_path.exists():
            abort(404)
        return send_from_directory(str(static_dir), filename)

    # Controlled image proxy: serve images from the project's pic and pic-raw dirs only
    @app.route('/static_image')
    def static_image():
        controller = app.epaper_controller
        if not controller:
            abort(404)

        path = request.args.get('path')
        if not path:
            abort(400)

        # Normalize and ensure the requested file is inside allowed directories
        from pathlib import Path
        p = Path(path).resolve()
        allowed_dirs = [controller.source_dir.resolve(), controller.output_dir.resolve()]
        for d in allowed_dirs:
            try:
                if d == p or d in p.parents:
                    return send_file(str(p))
            except Exception:
                continue

        abort(403)

    # Controlled shutdown endpoint (used by the controller to stop the server)
    @app.route('/__shutdown__', methods=['POST'])
    def _shutdown():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            return {"error": "Not running with the Werkzeug server"}, 500
        func()
        return {"message": "Server shutting down"}
    
    # Basic error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Endpoint not found"}, 404
        
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {"error": "Internal server error"}, 500
    
    return app

def start_server(epaper_controller=None, host='0.0.0.0', port=5000, debug=False, ssl=False, server_container=None):
    """
    Start the Flask web server
    
    Args:
        epaper_controller: Instance of ePaperController for display operations
        host: Host address to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to listen on (default: 5000)
        debug: Enable Flask debug mode (default: False)
    """
    app = create_app(epaper_controller)

    # Log resolved static dir for debugging
    try:
        module_dir = Path(__file__).resolve().parent
        static_dir = module_dir / 'static'
        logger.info(f"Serving static files from: {static_dir}")
    except Exception:
        pass

    # SSL context setup if enabled
    ssl_context = None
    if ssl:
        try:
            from pathlib import Path
            import ssl as ssl_module
            
            # Look for SSL certificates in config directory
            project_root = Path(__file__).resolve().parents[2]  # Go up from src/web/server.py to project root
            config_dir = project_root / 'config'
            cert_file = config_dir / 'raspberrypi.local.crt'
            key_file = config_dir / 'raspberrypi.local.key'
            
            if cert_file.exists() and key_file.exists():
                ssl_context = ssl_module.create_default_context(ssl_module.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(str(cert_file), str(key_file))
                logger.info(f"SSL enabled using certificates: {cert_file}")
                
                # If SSL is enabled, start both HTTP and HTTPS servers on standard ports
                if port == 5000:  # Default development port
                    # Start multiple servers for different access methods
                    import threading
                    
                    logger.info(f"Starting ePaper web servers:")
                    logger.info(f"  HTTP:       http://{host}:80")
                    logger.info(f"  HTTPS:      https://{host}:443") 
                    logger.info(f"  HTTP Dev:   http://{host}:5000")
                    
                    # Start HTTP server on port 80 in background thread
                    http_80_server = make_server(host, 80, app)
                    http_80_thread = threading.Thread(target=http_80_server.serve_forever, daemon=True)
                    http_80_thread.start()
                    
                    # Start HTTP development server on port 5000 in background thread  
                    http_dev_server = make_server(host, 5000, app)
                    http_dev_thread = threading.Thread(target=http_dev_server.serve_forever, daemon=True)
                    http_dev_thread.start()
                    
                    # Main thread runs HTTPS server on port 443
                    server = make_server(host, 443, app, ssl_context=ssl_context)
                else:
                    logger.info(f"Starting ePaper HTTPS server on {host}:{port}")
                    server = make_server(host, port, app, ssl_context=ssl_context)
            else:
                logger.warning(f"SSL certificates not found at {cert_file} and {key_file}")
                logger.warning("Falling back to HTTP mode")
                ssl_context = None
        except Exception as e:
            logger.error(f"Failed to setup SSL: {e}")
            logger.warning("Falling back to HTTP mode")
            ssl_context = None
    
    # Fallback to HTTP-only server
    if not ssl_context:
        logger.info(f"Starting ePaper web server on http://{host}:{port}")
        server = make_server(host, port, app)
    
    if server_container is not None and isinstance(server_container, dict):
        server_container['server'] = server

    try:
        server.serve_forever()
    finally:
        try:
            server.shutdown()
        except Exception:
            pass