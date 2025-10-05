"""
Path Utilities Module

Provides utilities for managing Python paths and library locations.
"""

import sys
from pathlib import Path


def setup_project_paths():
    """
    Add project directories to Python path for importing modules.
    
    Adds both the project root and the lib/ directory to sys.path
    if they're not already present. This allows importing from:
    - src/ modules (via project root)
    - lib/waveshare_epd (via lib directory)
    
    Returns:
        dict: Paths that were added with their purposes
    """
    project_root = Path(__file__).parent.parent
    lib_path = project_root / 'lib'
    
    added_paths = {}
    
    # Add project root for src/ imports
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        added_paths['project_root'] = str(project_root)
    
    # Add lib/ directory for waveshare_epd imports
    if str(lib_path) not in sys.path:
        sys.path.append(str(lib_path))
        added_paths['lib_path'] = str(lib_path)
    
    return added_paths


def get_project_root():
    """
    Get the project root directory path.
    
    Returns:
        Path: Project root directory
    """
    return Path(__file__).parent.parent


def get_lib_path():
    """
    Get the lib/ directory path.
    
    Returns:
        Path: lib/ directory path
    """
    return get_project_root() / 'lib'


if __name__ == "__main__":
    # Test path setup if run directly
    print("Setting up project paths...")
    added = setup_project_paths()
    
    if added:
        print("Added paths:")
        for purpose, path in added.items():
            print(f"  {purpose}: {path}")
    else:
        print("All paths already in sys.path")
    
    print(f"Project root: {get_project_root()}")
    print(f"Lib path: {get_lib_path()}")