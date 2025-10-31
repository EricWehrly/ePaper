"""
Filesystem Operations Module

Handles all file I/O operations with proper error handling, 
file locking awareness, and directory management.
"""

import os
import logging
import time
from pathlib import Path
from typing import List, Set, Optional, Union
import fcntl
import errno

logger = logging.getLogger(__name__)


class FileSystemError(Exception):
    """Custom exception for filesystem-related errors"""
    pass


def ensure_directory(directory_path: Union[str, Path]) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        bool: True if directory exists or was created successfully
        
    Raises:
        FileSystemError: If directory cannot be created
    """
    try:
        directory_path = Path(directory_path)
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
        
    except PermissionError:
        logger.error(f"Permission denied creating directory: {directory_path}")
        raise FileSystemError(f"Permission denied: {directory_path}")
        
    except OSError as e:
        logger.error(f"OS error creating directory {directory_path}: {e}")
        raise FileSystemError(f"Cannot create directory {directory_path}: {e}")


def scan_directory(directory_path: Union[str, Path], 
                  extensions: Optional[Set[str]] = None,
                  recursive: bool = False) -> List[Path]:
    """
    Scan directory for files with specified extensions.
    
    Args:
        directory_path: Path to directory to scan
        extensions: Set of file extensions to include (e.g., {'.jpg', '.png'})
                   If None, includes all files
        recursive: Whether to scan subdirectories recursively
        
    Returns:
        List of Path objects for matching files
        
    Raises:
        FileSystemError: If directory cannot be accessed
    """
    try:
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            logger.warning(f"Directory does not exist: {directory_path}")
            return []
            
        if not directory_path.is_dir():
            logger.warning(f"Path is not a directory: {directory_path}")
            return []
            
        files = []
        
        # Choose scanning method
        if recursive:
            pattern = "**/*"
            iterator = directory_path.rglob(pattern)
        else:
            iterator = directory_path.iterdir()
            
        for item in iterator:
            if item.is_file():
                # Check extension filter
                if extensions is None or item.suffix.lower() in extensions:
                    files.append(item)
                    
        # Sort for consistent ordering
        files.sort(key=lambda p: p.name.lower())
        
        return files
        
    except PermissionError:
        logger.error(f"Permission denied accessing directory: {directory_path}")
        raise FileSystemError(f"Permission denied: {directory_path}")
        
    except OSError as e:
        logger.error(f"OS error scanning directory {directory_path}: {e}")
        raise FileSystemError(f"Cannot scan directory {directory_path}: {e}")


def is_file_newer(file1: Union[str, Path], file2: Union[str, Path]) -> bool:
    """
    Check if file1 is newer than file2.
    
    Args:
        file1: Path to first file
        file2: Path to second file
        
    Returns:
        bool: True if file1 exists and is newer than file2, False otherwise
    """
    try:
        file1_path = Path(file1)
        file2_path = Path(file2)
        
        if not file1_path.exists() or not file2_path.exists():
            return False
            
        file1_time = file1_path.stat().st_mtime
        file2_time = file2_path.stat().st_mtime
        
        return file1_time > file2_time
        
    except OSError as e:
        return False


def safe_file_operation(operation, file_path: Union[str, Path], 
                       max_retries: int = 3, retry_delay: float = 0.1):
    """
    Perform a file operation with retry logic for handling busy files.
    
    Args:
        operation: Callable that performs the file operation
        file_path: Path to the file
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Result of the operation
        
    Raises:
        FileSystemError: If operation fails after all retries
    """
    file_path = Path(file_path)
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
            
        except (OSError, IOError) as e:
            if e.errno == errno.EBUSY or "being used by another process" in str(e).lower():
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"File remains busy after {max_retries} retries: {file_path}")
                    raise FileSystemError(f"File busy: {file_path}")
            else:
                # Other OS/IO errors - don't retry
                logger.error(f"File operation failed: {e}")
                raise FileSystemError(f"Operation failed on {file_path}: {e}")


def safe_read_file(file_path: Union[str, Path], mode: str = 'rb') -> bytes:
    """
    Safely read a file with error handling and busy file detection.
    
    Args:
        file_path: Path to the file to read
        mode: File open mode (default: 'rb' for binary)
        
    Returns:
        File contents as bytes or string
        
    Raises:
        FileSystemError: If file cannot be read
    """
    def read_operation():
        with open(file_path, mode) as f:
            return f.read()
    
    try:
        return safe_file_operation(read_operation, file_path)
        
    except FileSystemError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        raise FileSystemError(f"Cannot read file {file_path}: {e}")


def safe_write_file(file_path: Union[str, Path], data: Union[bytes, str], 
                   mode: str = 'wb') -> bool:
    """
    Safely write data to a file with error handling.
    
    Args:
        file_path: Path to the file to write
        data: Data to write
        mode: File open mode (default: 'wb' for binary)
        
    Returns:
        bool: True if successful
        
    Raises:
        FileSystemError: If file cannot be written
    """
    def write_operation():
        # Ensure parent directory exists
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, mode) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        
        return True
    
    try:
        return safe_file_operation(write_operation, file_path)
        
    except FileSystemError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing {file_path}: {e}")
        raise FileSystemError(f"Cannot write file {file_path}: {e}")


def safe_delete_file(file_path: Union[str, Path]) -> bool:
    """
    Safely delete a file with error handling.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        bool: True if successful or file doesn't exist
        
    Raises:
        FileSystemError: If file cannot be deleted
    """
    def delete_operation():
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            file_path_obj.unlink()
        return True
    
    try:
        return safe_file_operation(delete_operation, file_path)
        
    except FileSystemError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting {file_path}: {e}")
        raise FileSystemError(f"Cannot delete file {file_path}: {e}")


def check_file_lock(file_path: Union[str, Path]) -> bool:
    """
    Check if a file is locked by another process.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if file is locked, False if available or doesn't exist
    """
    try:
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return False
            
        # Try to open file for writing to test lock status
        with open(file_path, 'r+b') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return False  # Not locked
            except (OSError, IOError):
                return True  # Locked
                
    except (OSError, IOError):
        # Assume locked if we can't access it
        return True


def get_file_info(file_path: Union[str, Path]) -> Optional[dict]:
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        dict with file info (size, modified_time, etc.) or None if file doesn't exist
    """
    try:
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return None
            
        stat = file_path_obj.stat()
        
        return {
            'path': file_path_obj,
            'size': stat.st_size,
            'modified_time': stat.st_mtime,
            'created_time': stat.st_ctime,
            'is_file': file_path_obj.is_file(),
            'is_dir': file_path_obj.is_dir(),
            'extension': file_path_obj.suffix.lower(),
            'name': file_path_obj.name,
            'stem': file_path_obj.stem
        }
        
    except OSError as e:
        return None


def cleanup_old_files(directory_path: Union[str, Path], 
                     max_age_hours: float = 24,
                     extensions: Optional[Set[str]] = None) -> int:
    """
    Clean up old files in a directory.
    
    Args:
        directory_path: Path to directory to clean
        max_age_hours: Maximum age in hours before file is considered old
        extensions: Set of extensions to consider (None for all files)
        
    Returns:
        int: Number of files deleted
        
    Raises:
        FileSystemError: If cleanup fails
    """
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        files = scan_directory(directory_path, extensions)
        deleted_count = 0
        
        for file_path in files:
            file_info = get_file_info(file_path)
            if file_info and (current_time - file_info['modified_time']) > max_age_seconds:
                try:
                    safe_delete_file(file_path)
                    deleted_count += 1
                except FileSystemError as e:
                    logger.warning(f"Could not delete old file {file_path}: {e}")
                    
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old files from {directory_path}")
            
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during cleanup of {directory_path}: {e}")
        raise FileSystemError(f"Cleanup failed: {e}")


# Removed __main__ block - use cli.py test-filesystem command instead