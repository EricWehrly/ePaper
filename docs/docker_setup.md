# Docker Setup Guide for Google Photos Integration

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Google Cloud Project with Photos Picker API enabled
- OAuth 2.0 credentials downloaded

### Step-by-Step Setup

#### 1. Build and Start the Application
```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up epaper-display

# Or run in development mode with hot reload
docker-compose --profile dev up epaper-dev
```

#### 2. Set Up Google Cloud Project

**Create Google Cloud Project and Credentials:**

1. **Create Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "New Project" → Enter project name (e.g., "ePaper Display")
   - Note the Project ID (you'll need this)

2. **Enable APIs:**
   - Navigate to "APIs & Services" → "Library"  
   - Search for and enable: "Photos Library API"
   - Search for and enable: "Photos Picker API"

3. **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" (allows any Google user to authenticate)
   - Fill in required fields:
     - App name: "ePaper Photo Display" 
     - User support email: your email
     - Developer contact: your email
   - **Scopes**: Add `https://www.googleapis.com/auth/photospicker.mediaitems.readonly`
   - **Test Users**: Add your own email for initial testing

4. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: "Web application"
   - Name: "ePaper Display Client"
   - **Authorized redirect URIs**: Add these patterns:
     ```
     http://localhost:5000/oauth/callback
     http://127.0.0.1:5000/oauth/callback  
     http://your-pi-hostname.local:5000/oauth/callback
     http://your-actual-ip:5000/oauth/callback
     ```
   - Download the JSON credentials file

**Configure Credentials:**
```bash
# Copy your downloaded OAuth credentials (rename the file)
cp ~/Downloads/client_secret_*.json config/google_photos_credentials.json
```

**Update settings.json:**
Edit `config/settings.json` - **DO NOT hardcode hostname**:
```json
{
  "google_photos": {
    "client_id": "123456789-abcdef.apps.googleusercontent.com",
    "client_secret": "GOCSPX-your_actual_client_secret",
    "redirect_path": "/oauth/callback",
    "scopes": ["https://www.googleapis.com/auth/photospicker.mediaitems.readonly"]
  }
}
```

> **Note**: The `redirect_uri` will be built dynamically from the request host/port + `redirect_path`

#### 3. Access the Application
- **Web Interface**: http://localhost:5000
- **Development Mode**: http://localhost:5001 (if using dev profile)

### Docker Commands Reference

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f epaper-display

# Stop services
docker-compose down

# Development mode with hot reload
docker-compose --profile dev up

# Shell access to container
docker-compose exec epaper-display bash

# Rebuild after code changes
docker-compose build --no-cache
```

### Volume Mounts

The Docker setup automatically mounts:
- `./config` → Container config (for credentials)
- `./pic` → Converted images for display
- `./pic-raw` → Raw downloaded images
- `./logs` → Application logs

### Troubleshooting

#### Container Won't Start
```bash
# Check logs
docker-compose logs epaper-display

# Rebuild image
docker-compose build --no-cache
```

#### Google Photos Auth Issues
```bash
# Check if credentials file exists
ls -la config/google_photos_credentials.json

# View current settings
cat config/settings.json
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER ./config ./pic ./pic-raw ./logs
```

### Production Deployment

For production deployment, modify `docker-compose.yml`:

```yaml
services:
  epaper-display:
    build: .
    ports:
      - "80:5000"  # Use port 80
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
    restart: always
    volumes:
      - ./config:/app/config:ro  # Read-only config
      - epaper-pics:/app/pic
      - epaper-raw:/app/pic-raw
      - epaper-logs:/app/logs

volumes:
  epaper-pics:
  epaper-raw:
  epaper-logs:
```

---

## Next Steps

1. **Complete Google Cloud Setup** (see [Implementation Guide](./google_photos_implementation.md))
2. **Test Basic Photo Selection** 
3. **Integrate with Existing Conversion Pipeline**
4. **Add Batch Processing Features**