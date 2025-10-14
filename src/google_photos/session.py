"""
Session management for Google Photos integration.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)

@dataclass
class PhotoSession:
    """Represents a Google Photos picker session."""
    session_id: str
    picker_uri: str
    created_at: datetime
    status: str = "active"  # active, completed, expired, cancelled
    user_id: Optional[str] = None
    media_count: int = 0
    downloaded_files: List[str] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.downloaded_files is None:
            self.downloaded_files = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PhotoSession':
        """Create instance from dictionary."""
        data = data.copy()
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)

class SessionManager:
    """Manages Google Photos picker sessions."""
    
    def __init__(self, storage_path: str = "config/photo_sessions.json"):
        """
        Initialize session manager.
        
        Args:
            storage_path: Path to store session data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(exist_ok=True)
        self.sessions = {}
        self.load_sessions()
        
    def create_session(self, session_id: str, picker_uri: str, user_id: Optional[str] = None) -> PhotoSession:
        """
        Create and store a new session.
        
        Args:
            session_id: Google Photos session ID
            picker_uri: URI for photo picker
            user_id: Optional user identifier
            
        Returns:
            Created session object
        """
        session = PhotoSession(
            session_id=session_id,
            picker_uri=picker_uri,
            created_at=datetime.now(),
            user_id=user_id
        )
        
        self.sessions[session_id] = session
        self.save_sessions()
        
        logger.info(f"Created session {session_id} for user {user_id or 'anonymous'}")
        return session
    
    def get_session(self, session_id: str) -> Optional[PhotoSession]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session object if found
        """
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **updates) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session ID to update
            **updates: Fields to update
            
        Returns:
            True if session was updated
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
            
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
                
        self.save_sessions()
        logger.debug(f"Updated session {session_id}: {updates}")
        return True
    
    def mark_completed(self, session_id: str, media_count: int, downloaded_files: List[str]) -> bool:
        """
        Mark session as completed.
        
        Args:
            session_id: Session ID
            media_count: Number of media items selected
            downloaded_files: List of downloaded file paths
            
        Returns:
            True if session was updated
        """
        return self.update_session(
            session_id,
            status="completed",
            completed_at=datetime.now(),
            media_count=media_count,
            downloaded_files=downloaded_files
        )
    
    def mark_expired(self, session_id: str) -> bool:
        """Mark session as expired."""
        return self.update_session(session_id, status="expired")
    
    def mark_cancelled(self, session_id: str) -> bool:
        """Mark session as cancelled."""
        return self.update_session(session_id, status="cancelled")
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[PhotoSession]:
        """
        Get recent sessions for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions to return
            
        Returns:
            List of user's sessions, most recent first
        """
        user_sessions = [
            session for session in self.sessions.values()
            if session.user_id == user_id
        ]
        
        # Sort by creation time, most recent first
        user_sessions.sort(key=lambda s: s.created_at, reverse=True)
        
        return user_sessions[:limit]
    
    def get_active_sessions(self) -> List[PhotoSession]:
        """Get all active (non-completed) sessions."""
        return [
            session for session in self.sessions.values()
            if session.status == "active"
        ]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove old sessions to prevent storage bloat.
        
        Args:
            max_age_hours: Maximum age of sessions to keep
            
        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        old_session_ids = [
            session_id for session_id, session in self.sessions.items()
            if session.created_at < cutoff_time and session.status in ["completed", "expired", "cancelled"]
        ]
        
        for session_id in old_session_ids:
            del self.sessions[session_id]
            
        if old_session_ids:
            self.save_sessions()
            logger.info(f"Cleaned up {len(old_session_ids)} old sessions")
            
        return len(old_session_ids)
    
    def get_session_stats(self) -> Dict:
        """
        Get statistics about all sessions.
        
        Returns:
            Dictionary with session statistics
        """
        if not self.sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "completed_sessions": 0,
                "total_photos_downloaded": 0
            }
            
        sessions = list(self.sessions.values())
        
        return {
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s.status == "active"]),
            "completed_sessions": len([s for s in sessions if s.status == "completed"]),
            "expired_sessions": len([s for s in sessions if s.status == "expired"]),
            "cancelled_sessions": len([s for s in sessions if s.status == "cancelled"]),
            "total_photos_downloaded": sum(s.media_count for s in sessions if s.status == "completed"),
            "total_files_downloaded": sum(len(s.downloaded_files) for s in sessions if s.downloaded_files)
        }
    
    def load_sessions(self):
        """Load sessions from storage."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    session_data = json.load(f)
                    
                self.sessions = {
                    session_id: PhotoSession.from_dict(data)
                    for session_id, data in session_data.items()
                }
                
                logger.info(f"Loaded {len(self.sessions)} sessions from storage")
            else:
                logger.info("No existing session storage found, starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            self.sessions = {}
    
    def save_sessions(self):
        """Save sessions to storage."""
        try:
            session_data = {
                session_id: session.to_dict()
                for session_id, session in self.sessions.items()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            logger.debug(f"Saved {len(self.sessions)} sessions to storage")
            
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())