# Google Photos Integration - Phase 1 Implementation Guide

## Quick Start Checklist

### Prerequisites
- [ ] Google Cloud Project created
- [ ] Google Photos Picker API enabled
- [ ] OAuth 2.0 credentials configured  
- [ ] Development environment ready

### Implementation Steps
- [ ] Install dependencies
- [ ] Configure authentication
- [ ] Add API routes
- [ ] Create frontend interface
- [ ] Test end-to-end flow

---

## Detailed Setup Instructions

### 1. Google Cloud Project Setup

#### Enable APIs
```bash
# In Google Cloud Console or via gcloud CLI:
gcloud services enable photoslibrary.googleapis.com
gcloud services enable photospicker.googleapis.com
```

#### Create OAuth 2.0 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" > "Credentials"
3. Click "Create Credentials" > "OAuth 2.0 Client ID"
4. Choose "Web application"
5. Add authorized redirect URI: `http://localhost:5000/oauth/callback`
6. Download credentials JSON file

#### Required Scopes
```
https://www.googleapis.com/auth/photospicker.mediaitems.readonly
```

### 2. Project Dependencies

#### Add to requirements.txt
```txt
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
requests==2.31.0
```

#### Install
```bash
pip install -r requirements.txt
```

### 3. Configuration

#### Add to config/settings.json
```json
{
  "google_photos": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "client_secret": "your-client-secret", 
    "redirect_uri": "http://localhost:5000/oauth/callback",
    "scopes": ["https://www.googleapis.com/auth/photospicker.mediaitems.readonly"]
  }
}
```

**Security Note**: Never commit real credentials to git. Use environment variables in production.

---

## Code Implementation

### 1. Authentication Module

#### src/google_photos/auth.py
```python
import os
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

class GooglePhotosAuth:
    def __init__(self, config):
        self.client_id = config['client_id']
        self.client_secret = config['client_secret'] 
        self.redirect_uri = config['redirect_uri']
        self.scopes = config['scopes']
        
    def get_authorization_url(self):
        """Get URL to redirect user for OAuth consent."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [self.redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return auth_url, state
    
    def exchange_code_for_tokens(self, authorization_code, state):
        """Exchange authorization code for access tokens."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [self.redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth", 
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=self.scopes,
            state=state
        )
        flow.redirect_uri = self.redirect_uri
        
        flow.fetch_token(authorization_response=authorization_code)
        
        return flow.credentials
```

### 2. Picker API Interface

#### src/google_photos/picker.py
```python
import requests
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GooglePhotosPicker:
    def __init__(self, credentials):
        self.credentials = credentials
        self.base_url = "https://photospicker.googleapis.com/v1"
        
    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated request to Picker API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
        
    def create_session(self) -> Dict:
        """Create a new photo picking session."""
        try:
            result = self._make_request("POST", "sessions")
            logger.info(f"Created picker session: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
            
    def get_session(self, session_id: str) -> Dict:
        """Get current session status."""
        try:
            result = self._make_request("GET", f"sessions/{session_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise
            
    def list_media_items(self, session_id: str) -> List[Dict]:
        """List media items selected in session."""
        try:
            result = self._make_request(
                "GET", 
                "mediaItems", 
                params={"sessionId": session_id}
            )
            return result.get("mediaItems", [])
        except Exception as e:
            logger.error(f"Failed to list media items for session {session_id}: {e}")
            raise
            
    def poll_until_complete(self, session_id: str, timeout: int = 300) -> bool:
        """Poll session until user completes selection or timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            session = self.get_session(session_id)
            
            if session.get("mediaItemsSet", False):
                logger.info(f"Session {session_id} completed successfully")
                return True
                
            # Use recommended polling interval from response
            polling_config = session.get("pollingConfig", {})
            interval = polling_config.get("pollInterval", "10s")
            
            # Parse interval (format: "10s", "30s", etc.)
            seconds = int(interval.replace("s", ""))
            time.sleep(seconds)
            
        logger.warning(f"Session {session_id} timed out after {timeout} seconds")
        return False
```

### 3. Download Manager

#### src/google_photos/downloader.py
```python
import os
import requests
import logging
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class GooglePhotosDownloader:
    def __init__(self, credentials, download_dir: str = "pic-raw"):
        self.credentials = credentials
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
    def download_media_item(self, media_item: Dict) -> Optional[str]:
        """Download a single media item and return local file path."""
        try:
            # Get download URL with full resolution
            base_url = media_item["mediaFile"]["baseUrl"] 
            download_url = f"{base_url}=d"  # 'd' parameter for full download
            
            # Make authenticated request
            headers = {
                "Authorization": f"Bearer {self.credentials.token}"
            }
            
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Generate filename
            filename = self._generate_filename(media_item)
            file_path = self.download_dir / filename
            
            # Save file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Downloaded: {filename}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to download media item: {e}")
            return None
            
    def download_all(self, media_items: List[Dict]) -> List[str]:
        """Download all media items and return list of file paths."""
        downloaded_paths = []
        
        for item in media_items:
            path = self.download_media_item(item)
            if path:
                downloaded_paths.append(path)
                
        logger.info(f"Downloaded {len(downloaded_paths)} of {len(media_items)} items")
        return downloaded_paths
        
    def _generate_filename(self, media_item: Dict) -> str:
        """Generate filename for downloaded media item."""
        # Try to use original filename if available
        filename = media_item.get("filename", "unknown")
        
        # If no extension, add one based on MIME type
        if '.' not in filename:
            mime_type = media_item["mediaFile"].get("mimeType", "")
            if "jpeg" in mime_type:
                filename += ".jpg"
            elif "png" in mime_type:
                filename += ".png"
            else:
                filename += ".jpg"  # Default fallback
                
        return filename
```

### 4. Flask Route Integration

#### src/web/routes.py additions
```python
from flask import request, jsonify, redirect, session, url_for
from src.google_photos.auth import GooglePhotosAuth
from src.google_photos.picker import GooglePhotosPicker  
from src.google_photos.downloader import GooglePhotosDownloader
import json

# Load config
with open('config/settings.json', 'r') as f:
    config = json.load(f)

google_auth = GooglePhotosAuth(config['google_photos'])

@app.route('/api/google-photos/auth/start')
def start_google_auth():
    """Start Google Photos OAuth flow."""
    auth_url, state = google_auth.get_authorization_url()
    session['oauth_state'] = state
    return jsonify({"auth_url": auth_url})

@app.route('/oauth/callback')  
def oauth_callback():
    """Handle OAuth callback from Google."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if state != session.get('oauth_state'):
        return "Invalid state parameter", 400
        
    try:
        credentials = google_auth.exchange_code_for_tokens(code, state)
        session['google_credentials'] = credentials_to_dict(credentials)
        return redirect('/google-photos-success')
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return f"Authentication failed: {e}", 500

@app.route('/api/google-photos/session', methods=['POST'])
def create_picker_session():
    """Create a new Google Photos picker session."""
    credentials = dict_to_credentials(session.get('google_credentials'))
    if not credentials:
        return jsonify({"error": "Not authenticated"}), 401
        
    try:
        picker = GooglePhotosPicker(credentials)
        session_data = picker.create_session()
        
        return jsonify({
            "session_id": session_data["id"],
            "picker_uri": session_data["pickerUri"]
        })
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/google-photos/session/<session_id>/poll')
def poll_session(session_id):
    """Poll session status."""
    credentials = dict_to_credentials(session.get('google_credentials'))
    if not credentials:
        return jsonify({"error": "Not authenticated"}), 401
        
    try:
        picker = GooglePhotosPicker(credentials)
        session_data = picker.get_session(session_id)
        
        return jsonify({
            "completed": session_data.get("mediaItemsSet", False),
            "polling_interval": session_data.get("pollingConfig", {}).get("pollInterval", "10s")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/google-photos/download/<session_id>', methods=['POST'])
def download_selected_photos(session_id):
    """Download photos selected in session."""
    credentials = dict_to_credentials(session.get('google_credentials'))
    if not credentials:
        return jsonify({"error": "Not authenticated"}), 401
        
    try:
        picker = GooglePhotosPicker(credentials)
        media_items = picker.list_media_items(session_id)
        
        if not media_items:
            return jsonify({"message": "No photos selected"}), 200
            
        downloader = GooglePhotosDownloader(credentials)
        downloaded_paths = downloader.download_all(media_items)
        
        return jsonify({
            "message": f"Downloaded {len(downloaded_paths)} photos",
            "files": downloaded_paths
        })
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return jsonify({"error": str(e)}), 500

# Helper functions
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def dict_to_credentials(credentials_dict):
    if not credentials_dict:
        return None
    # Implementation depends on google-auth library version
    # See documentation for proper deserialization
    pass
```

### 5. Frontend Interface

#### src/web/static/google-photos.js
```javascript
class GooglePhotosIntegration {
    constructor() {
        this.currentSessionId = null;
        this.pollingInterval = null;
    }
    
    async startAuthentication() {
        try {
            const response = await fetch('/api/google-photos/auth/start');
            const data = await response.json();
            
            // Open authentication in new window
            window.open(data.auth_url, 'google-auth', 'width=500,height=600');
            
            // Listen for completion (implement postMessage communication)
            this.waitForAuthCompletion();
        } catch (error) {
            console.error('Auth start failed:', error);
        }
    }
    
    async createSession() {
        try {
            const response = await fetch('/api/google-photos/session', {
                method: 'POST'
            });
            const data = await response.json();
            
            this.currentSessionId = data.session_id;
            this.displayPickerInterface(data.picker_uri);
            this.startPolling();
            
        } catch (error) {
            console.error('Session creation failed:', error);
        }
    }
    
    displayPickerInterface(pickerUri) {
        // Show QR code and link
        const container = document.getElementById('google-photos-picker');
        container.innerHTML = `
            <div class="picker-interface">
                <h3>Select Photos from Google Photos</h3>
                <div class="qr-code">
                    <canvas id="qr-canvas"></canvas>
                    <p>Scan with your phone</p>
                </div>
                <div class="direct-link">
                    <a href="${pickerUri}" target="_blank" class="btn btn-primary">
                        Open Google Photos
                    </a>
                </div>
                <div class="status" id="selection-status">
                    Waiting for photo selection...
                </div>
            </div>
        `;
        
        // Generate QR code (you'll need a QR code library)
        this.generateQRCode(pickerUri);
    }
    
    startPolling() {
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/google-photos/session/${this.currentSessionId}/poll`);
                const data = await response.json();
                
                if (data.completed) {
                    this.stopPolling();
                    this.downloadSelectedPhotos();
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 10000); // Poll every 10 seconds
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    async downloadSelectedPhotos() {
        try {
            document.getElementById('selection-status').textContent = 'Downloading photos...';
            
            const response = await fetch(`/api/google-photos/download/${this.currentSessionId}`, {
                method: 'POST'
            });
            const data = await response.json();
            
            document.getElementById('selection-status').textContent = data.message;
            
            // Refresh the photo list or trigger conversion
            this.refreshPhotoList();
            
        } catch (error) {
            console.error('Download failed:', error);
            document.getElementById('selection-status').textContent = 'Download failed. Please try again.';
        }
    }
    
    refreshPhotoList() {
        // Trigger refresh of existing photo list UI
        // This depends on your current frontend implementation
        window.location.reload(); // Simple approach
    }
    
    generateQRCode(url) {
        // Implement QR code generation
        // You can use libraries like 'qrious' or 'qrcode.js'
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.googlePhotos = new GooglePhotosIntegration();
});
```

### 6. HTML Template

#### src/web/templates/google-photos-picker.html
```html
<!DOCTYPE html>
<html>
<head>
    <title>Google Photos Integration</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>Add Photos from Google Photos</h1>
        
        <div id="auth-section">
            <p>Connect to Google Photos to select and download your photos.</p>
            <button onclick="googlePhotos.startAuthentication()" class="btn btn-primary">
                Connect to Google Photos
            </button>
        </div>
        
        <div id="google-photos-picker" style="display: none;"></div>
        
        <div class="back-link">
            <a href="/">← Back to Main</a>
        </div>
    </div>
    
    <script src="/static/google-photos.js"></script>
</body>
</html>
```

---

## Testing Checklist

### Unit Tests
- [ ] Authentication flow works with test credentials
- [ ] Session creation returns valid session ID and picker URI
- [ ] Media item listing works with completed session
- [ ] Download saves files to correct location

### Integration Tests  
- [ ] Full OAuth flow completes successfully
- [ ] QR code opens Google Photos correctly
- [ ] Photo selection and download works end-to-end
- [ ] Error handling works for network issues

### User Acceptance Tests
- [ ] Non-technical user can complete photo selection
- [ ] Process works on both mobile and desktop
- [ ] Clear error messages for common issues
- [ ] Photos appear in conversion queue after download

---

## Common Issues & Solutions

### OAuth Verification
**Issue**: "This app isn't verified" warning  
**Solution**: For development, click "Advanced" → "Go to [app name] (unsafe)". For production, submit app for verification.

### Rate Limiting  
**Issue**: 429 Too Many Requests errors  
**Solution**: Implement exponential backoff, reduce request frequency

### CORS Issues
**Issue**: Frontend can't make requests to API  
**Solution**: Configure Flask-CORS properly, ensure proper headers

### Mobile UX Issues
**Issue**: QR code scanning doesn't work well  
**Solution**: Provide direct link as fallback, optimize QR code size

---

This implementation guide provides everything needed to get Phase 1 working. Once this basic flow is operational, you can move on to the enhancements in subsequent phases.