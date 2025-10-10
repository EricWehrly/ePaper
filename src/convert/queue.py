"""
Conversion queue management for ePaper display

Manages a queue of images to be converted from source formats to the 6-color
ePaper display format. Processes conversions sequentially in the background.
"""

import logging
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

class QueueStatus(Enum):
    """Status values for queue items"""
    PENDING = "pending"
    IN_PROGRESS = "in-progress" 
    COMPLETED = "completed"
    FAILED = "failed"

class QueueItem:
    """Individual item in the conversion queue"""
    
    def __init__(self, source_path: Path, output_path: Path):
        self.id = str(uuid.uuid4())
        self.filename = source_path.name
        self.source_path = source_path
        self.output_path = output_path
        self.status = QueueStatus.PENDING
        self.error = None
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "filename": self.filename,
            "source_path": str(self.source_path),
            "output_path": str(self.output_path),
            "status": self.status.value,
            "error": self.error,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueItem':
        """Create from dictionary for deserialization"""
        item = cls(Path(data["source_path"]), Path(data["output_path"]))
        item.id = data["id"]
        item.filename = data["filename"]
        item.status = QueueStatus(data["status"])
        item.error = data.get("error")
        item.timestamp = data["timestamp"]
        return item

class ConversionQueue:
    """Manages the conversion queue with background processing"""
    
    def __init__(self, controller, queue_file: Optional[Path] = None):
        self.controller = controller
        self.queue_file = queue_file or (controller.config_dir / 'queue.json')
        
        self._queue: List[QueueItem] = []
        self._lock = threading.RLock()
        self._worker_thread = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Load persisted queue state
        self._load_queue()
        
    def _load_queue(self):
        """Load queue state from disk"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    
                items = []
                for item_data in data.get("items", []):
                    try:
                        item = QueueItem.from_dict(item_data)
                        # Reset in-progress items to pending on startup
                        if item.status == QueueStatus.IN_PROGRESS:
                            item.status = QueueStatus.PENDING
                        items.append(item)
                    except Exception as e:
                        logger.warning(f"Failed to load queue item: {e}")
                        
                self._queue = items
                logger.info(f"Loaded {len(items)} items from queue")
        except Exception as e:
            logger.warning(f"Failed to load queue: {e}")
    
    def _save_queue(self):
        """Save queue state to disk"""
        try:
            with self._lock:
                data = {
                    "items": [item.to_dict() for item in self._queue],
                    "timestamp": time.time()
                }
                
                # Atomic write
                temp_file = self.queue_file.with_suffix('.json.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2)
                temp_file.replace(self.queue_file)
                
        except Exception as e:
            logger.warning(f"Failed to save queue: {e}")
    
    def add_file(self, source_path: Path) -> str:
        """Add a file to the conversion queue"""
        # Generate output path
        output_name = source_path.stem + '.bmp'
        output_path = self.controller.output_dir / output_name
        
        with self._lock:
            # Check if already in queue or completed
            for item in self._queue:
                if item.source_path == source_path:
                    logger.info(f"File {source_path.name} already in queue")
                    return item.id
            
            # Add new item
            item = QueueItem(source_path, output_path)
            self._queue.append(item)
            self._save_queue()
            
            logger.info(f"Added {source_path.name} to conversion queue (id: {item.id})")
            
            # Start processing if not already running
            if not self._running:
                self.start_processing()
                
            return item.id
    
    def get_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        with self._lock:
            return {
                "items": [item.to_dict() for item in self._queue],
                "total": len(self._queue),
                "pending": len([i for i in self._queue if i.status == QueueStatus.PENDING]),
                "in_progress": len([i for i in self._queue if i.status == QueueStatus.IN_PROGRESS]),
                "completed": len([i for i in self._queue if i.status == QueueStatus.COMPLETED]),
                "failed": len([i for i in self._queue if i.status == QueueStatus.FAILED]),
                "running": self._running
            }
    
    def start_processing(self):
        """Start the background processing thread"""
        if self._running:
            return
            
        self._stop_event.clear()
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Conversion queue processing started")
    
    def stop_processing(self):
        """Stop the background processing thread"""
        if not self._running:
            return
            
        self._running = False
        self._stop_event.set()
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
            
        logger.info("Conversion queue processing stopped")
    
    def _worker_loop(self):
        """Background worker thread loop"""
        while self._running and not self._stop_event.is_set():
            try:
                # Find next pending item
                next_item = None
                with self._lock:
                    for item in self._queue:
                        if item.status == QueueStatus.PENDING:
                            next_item = item
                            item.status = QueueStatus.IN_PROGRESS
                            break
                
                if next_item is None:
                    # No pending items, sleep and check again
                    time.sleep(2)
                    continue
                
                self._save_queue()
                logger.info(f"Converting {next_item.filename}...")
                
                # Perform the conversion
                success = self._convert_item(next_item)
                
                with self._lock:
                    if success:
                        next_item.status = QueueStatus.COMPLETED
                        logger.info(f"Converted {next_item.filename} successfully")
                    else:
                        next_item.status = QueueStatus.FAILED
                        logger.error(f"Failed to convert {next_item.filename}")
                
                self._save_queue()
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(1)
    
    def _convert_item(self, item: QueueItem) -> bool:
        """Convert a single item"""
        try:
            # Check if source file exists
            if not item.source_path.exists():
                item.error = "Source file not found"
                return False
            
            # Use the existing convert module
            from src.convert.core import convert_image
            
            # Perform conversion
            convert_image(
                input_path=item.source_path,
                output_path=item.output_path
            )
            
            # Verify output file was created
            if not item.output_path.exists():
                item.error = "Output file not created"
                return False
                
            return True
            
        except Exception as e:
            item.error = str(e)
            logger.error(f"Conversion failed for {item.filename}: {e}")
            return False
    
    def clear_completed(self):
        """Remove completed items from queue"""
        with self._lock:
            original_count = len(self._queue)
            self._queue = [item for item in self._queue if item.status != QueueStatus.COMPLETED]
            removed = original_count - len(self._queue)
            
            if removed > 0:
                self._save_queue()
                logger.info(f"Cleared {removed} completed items from queue")
    
    def clear_all(self):
        """Clear all items from queue (except in-progress)"""
        with self._lock:
            original_count = len(self._queue)
            self._queue = [item for item in self._queue if item.status == QueueStatus.IN_PROGRESS]
            removed = original_count - len(self._queue)
            
            if removed > 0:
                self._save_queue()
                logger.info(f"Cleared {removed} items from queue")
    
    def remove_item(self, item_id: str) -> bool:
        """Remove specific item from queue"""
        with self._lock:
            for i, item in enumerate(self._queue):
                if item.id == item_id and item.status != QueueStatus.IN_PROGRESS:
                    del self._queue[i]
                    self._save_queue()
                    logger.info(f"Removed item {item_id} from queue")
                    return True
            return False