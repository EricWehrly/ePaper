"""
ePaper Display Project

A Python project for displaying images on a Waveshare 4inch e-Paper HAT+ (E).
"""

__version__ = "0.1.0"
__author__ = "ePaper Project"

# Make modules easily importable
from . import convert
from . import filesystem
from . import display

__all__ = ['convert', 'filesystem', 'display']