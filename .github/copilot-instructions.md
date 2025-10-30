# ePaper Display Project

## Overview
A minimal Python project to display images on a Waveshare 4-inch e-Paper HAT+ (E) using Raspberry Pi

## Hardware Specifications
- **Device**: Waveshare 4-inch e-Paper HAT+ (E)
- **Resolution**: 400 x 600 pixels
- **Colors**: 6-color palette (BLACK, WHITE, YELLOW, RED, BLUE, GREEN)
- **Platform**: Raspberry Pi

## Development Setup

### Docker (Recommended)
```bash
# Add user to docker group (one time setup - requires logout/login)
sudo usermod -aG docker $USER

# Quick start with Docker
sudo docker compose up --build -d

# View logs
sudo docker compose logs -f

# Stop container
sudo docker compose down

# Access web interface: http://localhost:5000
```

**Note**: The service runs gracefully without the e-Paper display hardware. When the display is not connected:
- Web interface and APIs remain fully functional
- Image conversion and processing work normally  
- Google Photos integration operates independently
- Display operations return HTTP 503 "Display hardware not available"
- No process crashes or service interruptions

### Google Photos Development
```bash
# 1. Start Docker container
sudo docker compose up --build -d

# 2. Configure Google Photos credentials
# - Create Google Cloud project & enable Photos Picker API
# - Copy OAuth credentials to config/google_photos_credentials.json
# - See docs/google_photos_implementation.md for detailed setup

# 3. Test Google Photos integration
curl http://localhost:5000/api/google-photos/status

# 4. Access web UI for photo selection
# Open http://localhost:5000 in browser
```

### Manual Setup (Alternative)
```bash
# Traditional virtual environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m src.main --mode=web
```

## Project Structure
```
/home/eric/Projects/ePaper/
├── lib/waveshare_epd/     # Waveshare library
│   └── epd4in0e.py       # Device driver
├── pic/                  # BMP images for display
├── pic-raw/              # Source images (PNG, JPEG)
└── src/                  # Python scripts
    └── epd_4in0e_test.py # Reference example
```

## Core Requirements
1. **Image Loading**: Load PNG/JPEG images from `pic-raw/` folder (local upload or Google Photos)
2. **Image Processing**: 
   - Convert to 400x600 resolution
   - Apply 6-color palette (BLACK, WHITE, YELLOW, RED, BLUE, GREEN)
   - Save as BMP in `pic/` folder
3. **Display Cycling**: Automatically cycle through BMP images and display on e-paper
4. **Google Photos Integration**: Select and download photos using Google Photos Picker API

## Google Photos Setup
1. **Configure OAuth**: Copy credentials to `config/google_photos_credentials.json`
2. **Update settings**: Edit `config/settings.json` with your client ID/secret
3. **Test integration**: Use web interface to select photos from Google Photos
4. **See docs**: Full setup guide in `docs/docker_setup.md` and `docs/google_photos_implementation.md`

## Key Implementation Notes
- Use existing `waveshare_epd.epd4in0e` library
- Color constants: `epd.BLACK`, `epd.WHITE`, `epd.YELLOW`, `epd.RED`, `epd.BLUE`, `epd.GREEN`
- Device resolution: `epd.width` (400) x `epd.height` (600)
- Always call `epd.sleep()` when finished to preserve display

## Google Photos Integration Status

### Phase 1: Complete Photo Selection Interface ✅
- ✅ Docker environment setup complete
- ✅ Dependencies and module structure ready
- ✅ Web server integration working
- ✅ OAuth 2.0 authentication system implemented
- ✅ Google Photos Library API integration complete
- ✅ Photo selection interface with frontend/backend
- ✅ Download and conversion pipeline integration
- ✅ Display-optional architecture (works without hardware)

### Ready for Use
1. Configure Google Cloud project (see docs/google_photos_implementation.md)
2. Add OAuth credentials to config/google_photos_credentials.json
3. Access web interface: http://localhost:5000
4. Complete documentation: docs/google_photos_complete.md

## Code Style
- Keep functions simple and focused
- Use clear variable names
- **Minimal logging**: Only log errors, warnings, and major workflow steps
- Handle exceptions gracefully
- Avoid cluttering code with debug/info logs for routine operations

## Logging Guidelines
- **ERROR**: For failures that prevent operation
- **WARNING**: For recoverable issues or missing resources
- **INFO**: Only for major workflow milestones (startup, conversion batches, shutdown)
- **DEBUG**: Avoid unless specifically debugging
- **No logging for**: Successful routine operations, file I/O, basic function entry/exit
