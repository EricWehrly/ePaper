"""
Web server module for ePaper display control

This module provides web-based API endpoints for controlling the ePaper display,
allowing remote image management and display control through HTTP requests.
"""

from .server import create_app, start_server
from .routes import register_routes

__all__ = ['create_app', 'start_server', 'register_routes']