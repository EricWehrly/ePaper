"""
API utilities for Flask routes

Provides common decorators and utilities to reduce code duplication
in API endpoints.
"""

import logging
import functools
from flask import jsonify, current_app
from pathlib import Path

logger = logging.getLogger(__name__)

# Common file extensions used throughout the application
SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'}

def api_route(require_controller=True, require_display=False):
    """
    Decorator for API routes with common error handling and validation.
    
    Args:
        require_controller (bool): Whether controller must be initialized
        require_display (bool): Whether display manager must be initialized
    
    Returns:
        Decorated function with standardized error handling
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate controller initialization if required
                if require_controller:
                    controller = getattr(current_app, 'epaper_controller', None)
                    if not controller:
                        return create_error_response("Controller not initialized", 500)
                    
                    # Validate display hardware if required
                    if require_display and not controller.display_available:
                        return create_error_response("Display hardware not available", 503)
                    
                    # Check if display is busy for display operations
                    if require_display and controller.is_busy():
                        return create_error_response("Display busy", 409)
                
                # Call the actual route function
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"API route {func.__name__} failed: {e}")
                return create_error_response(str(e), 500)
        
        return wrapper
    return decorator

def create_success_response(data=None, message=None):
    """
    Create standardized success response.
    
    Args:
        data (dict): Response data
        message (str): Success message
    
    Returns:
        Flask JSON response
    """
    response = {"success": True}
    if data:
        response.update(data)
    if message:
        response["message"] = message
    return jsonify(response)

def create_error_response(error_message, status_code=400):
    """
    Create standardized error response.
    
    Args:
        error_message (str): Error description
        status_code (int): HTTP status code
    
    Returns:
        Flask JSON response with error status
    """
    return jsonify({"error": error_message}), status_code

def validate_image_file(filename):
    """
    Validate if filename has supported image extension.
    
    Args:
        filename (str): Filename to validate
    
    Returns:
        bool: True if valid image file
    """
    if not filename:
        return False
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS)

def count_files_by_extension(directory, extensions):
    """
    Count files in directory matching given extensions.
    
    Args:
        directory (Path): Directory to scan
        extensions (set): Set of file extensions to match
    
    Returns:
        int: Number of matching files
    """
    if not directory.exists():
        return 0
    
    count = 0
    for ext in extensions:
        count += len(list(directory.glob(f"*{ext}")))
    return count

def get_controller():
    """
    Get the ePaper controller from current app.
    
    Returns:
        ePaperController: Controller instance or None
    """
    return getattr(current_app, 'epaper_controller', None)

def safe_int(value, default=None, minimum=None):
    """
    Safely convert value to integer with validation.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        minimum: Minimum allowed value
    
    Returns:
        int: Converted integer or default
    """
    try:
        result = int(value)
        if minimum is not None and result < minimum:
            return default
        return result
    except (ValueError, TypeError):
        return default