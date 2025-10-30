# ePaper Display - Current Roadmap

**Current Sprint Focus**: System service setup and quality improvements

---

## 🎯 IMMEDIATE PRIORITIES

### Image Conversion Quality Testing
- **Status**: PLANNED - HIGH PRIORITY
- **Description**: Compare conversion quality between different source formats
- **Details**: 
  - Test JPG vs PNG source quality after conversion to 6-color ePaper
  - Document optimal source format recommendations  
  - TODO: Add HEIC format testing (when Google stops being weird about it)
- **Implementation**: Set up side-by-side visual comparison system

### System Service Installation
- **Status**: PLANNED - HIGH PRIORITY  
- **Description**: Create install/uninstall scripts for Pi system service
- **Details**:
  - Systemd service configuration
  - Auto-start on boot functionality
  - Proper service lifecycle management
  - Clean uninstall process

### Duplicate Detection System
- **Status**: IN PROGRESS
- **Description**: Prevent duplicate photo uploads
- **Current**: Framework created in `photo_validation.js` 
- **Next**: Implement hash comparison and user confirmation dialogs

---

## 📋 UPCOMING FEATURES

### Albums & Collections System
- **Priority**: MEDIUM
- **Description**: Create curated sets of images for cycling
- **Features**:
  - Custom image collections/albums
  - Album-specific slideshow mode
  - Favorite image management
  - Collection-based scheduling

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

## 🔧 TECHNICAL DEBT & UX IMPROVEMENTS

### Timer System Overhaul
- **Issue**: Autoplay timer includes display draw time, causing inconsistent intervals
- **Fix**: Timer should only measure image display duration, not processing time
- **Priority**: HIGH

### User Interface Polish
- **Prev/Next Button Feedback**: Add visual/audio feedback for navigation actions
- **Display Busy Indicator**: Move from lower-left to middle-top position  
- **Active Image Indicator**: Show which image is currently selected/displayed
- **Priority**: MEDIUM

### Performance Optimization
- **RequestAnimationFrame**: Implement for smoother frontend animations
- **WebSocket Integration**: Reduce server polling pressure with real-time updates
- **Worker Threads**: Explore background processing for heavy operations
- **Priority**: LOW-MEDIUM

---

## 📊 PROJECT STATUS

**Core Features**: ✅ Complete (ePaper display, web interface, drag & drop, Google Photos, conversion pipeline, Docker/SSL)  
**Current Phase**: System integration and quality improvements  
**Architecture**: Production-ready with containerized deployment

---

## 🚀 DEVELOPMENT WORKFLOW

### Current Focus
1. **Format Testing Setup**: Create visual comparison tools for JPG vs PNG conversion quality
2. **System Service**: Complete Pi service installation scripts
3. **Duplicate Detection**: Finish implementation of photo validation system

### Next Phase Planning  
1. **User Experience**: Address timer inconsistencies and interface polish
2. **Feature Expansion**: Begin albums/collections system design  
3. **Performance**: Implement WebSocket updates and frontend optimization

### Technical Standards
- **Incremental commits**: Small, focused changes for easier review
- **Documentation**: Update roadmap with each completed feature
- **Testing**: Manual verification on actual ePaper hardware
- **Code quality**: Maintain shared module architecture and clean separation

---

## 📝 NOTES

- **Google Photos**: Integration is complete and stable
- **Hardware**: All features designed to work gracefully without ePaper hardware connected
- **Deployment**: Docker environment handles all dependencies and service management
- **Architecture**: Shared upload modules established for consistent file handling across all input sources