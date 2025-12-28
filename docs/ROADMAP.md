# ePaper Display - Current Roadmap

**Current Sprint Focus**: Albums/playlists system and UX improvements

---

## 🎯 IMMEDIATE PRIORITIES

### Albums & Playlists System
- **Status**: IN PROGRESS - HIGH PRIORITY (Active Branch: playlist)
- **Description**: Create curated image collections for organized photo management
- **Features**:
  - Custom image albums/playlists
  - Album-based slideshow mode
  - Drag-and-drop photo organization (including multiple images at once)
  - Album metadata (title, description, created date)
  - Quick album switching in UI

### System Service Installation
- **Status**: PLANNED - HIGH PRIORITY  
- **Description**: Create install/uninstall scripts for Pi system service
- **Details**:
  - Docker-based deployment
  - Systemd service configuration
  - Auto-start on boot functionality
  - Proper service lifecycle management
  - Clean uninstall process

---

## 📋 PLANNED FEATURES

### Smoother Library Loading
- **Priority**: MEDIUM  
- **Description**: Fix image loading UX issues in library view
- **Issues**:
  - Images showing 'broken image' icon before loading
  - Dynamic scroll bar adjustment causing unintended page jumps
  - No visual loading indicators
- **Solutions**:
  - Hide images until fully loaded
  - Reserve space for images to prevent layout shifts
  - Add spinner/loading indicators
  - Show console/toast errors for failed loads with visual cues

### Library Sort & Filter
- **Priority**: MEDIUM
- **Description**: Enhanced organization and discovery
- **Features**:
  - Tag images for filtering (person, object, place from metadata)
  - Sort options (date, name, size, etc.)
  - Search functionality

### Conversion Preset System
- **Priority**: MEDIUM
- **Description**: User-selectable conversion configurations
- **Features**:
  - Legacy conversion settings for comparison testing
  - High contrast, soft enhancement, and other quality presets
  - Web UI integration for preset selection
  - A/B testing interface for quality comparison
  - Per-image-type preference saving

### Duplicate Detection System
- **Priority**: LOW
- **Description**: Prevent duplicate photo uploads
- **Current**: Framework created in `photo_validation.js` 
- **Next**: Implement hash comparison and user confirmation dialogs

### Color Palette Customization
- **Priority**: NICE TO HAVE
- **Description**: User-selectable color themes
- **Location**: Top-right interface area
- **Features**:
  - Dark/light mode toggle
  - Custom color picker
  - LocalStorage persistence
  - Live preview

---

## 🎨 UI IMPROVEMENTS

### Google Photos Icon
- **Priority**: LOW
- **Description**: Change "Photos" tab icon to recognizable Google Photos icon for clarity

### User Interface Polish
- **Priority**: MEDIUM
- **Description**: Improve feedback and visual indicators
- **Items**:
  - Prev/Next button feedback (visual/audio)
  - Display busy indicator repositioned (lower-left → middle-top)
  - Active image indicator showing current selection

---

## 🔧 TECHNICAL DEBT

### Timer System Overhaul
- **Priority**: HIGH
- **Issue**: Autoplay timer includes display draw time, causing inconsistent intervals
- **Fix**: Timer should only measure image display duration, not processing time


### Performance Optimization
- **Priority**: LOW-MEDIUM
- **Items**:
  - RequestAnimationFrame for smoother frontend animations
  - WebSocket integration to reduce server polling pressure
  - Worker threads for background processing (heavy work already on backend)

---

## 📊 PROJECT STATUS

**Core Features**: ✅ Complete (ePaper display, web interface, drag & drop, Google Photos, Docker/SSL)  
**Performance**: ✅ Conversion optimized (110x faster: 29.7s → 0.27s via PIL quantization)  
**Current Phase**: Albums/playlist system development  
**Architecture**: Production-ready with containerized deployment

---

## 📝 NOTES

- **Google Photos**: Integration complete and stable
- **Hardware**: All features work gracefully without ePaper hardware connected
- **Deployment**: Docker environment handles all dependencies and service management
- **Architecture**: Shared upload modules for consistent file handling across all input sources
- **Testing**: Integration tests via Playwright, unit tests via pytest
