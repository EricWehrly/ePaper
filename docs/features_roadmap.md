# Features Roadmap

This document outlines planned functional features for the ePaper Display system.

## 📁 Content Management

### Duplicate Photo Detection
**Status**: In Progress - High Priority  
**Description**: Prevent uploading the same photo multiple times by detecting duplicates.

**Implementation Ideas**:
- File hash comparison (MD5/SHA1 of image content)
- Filename + size comparison for quick checks  
- Visual duplicate detection using image fingerprinting
- User confirmation dialog for potential duplicates
- Option to replace vs. keep both versions

**Technical Notes**:
- Affects both drag-and-drop uploads and Google Photos downloads
- Framework implemented in shared photo_validation.js module
- TODO: Complete hash comparison and user confirmation dialogs

### Image Preview for Google Photos
**Status**: Planned - Medium Priority
**Description**: Show low-opacity image previews during Google Photos conversion (like drag-and-drop has).

**Implementation Ideas**:
- Use /static_image endpoint to serve raw downloaded images
- Apply same CSS overlay system as drag-and-drop
- Show preview immediately after download, before conversion

### Image Format Quality Testing
**Status**: Planned - High Priority
**Description**: Test and compare conversion quality between different source image formats.

**Implementation Ideas**:
- Side-by-side visual comparison of JPG vs PNG source conversions
- Quality metrics and recommendations for optimal source formats
- Visual test interface for manual quality assessment
- TODO: Add HEIC format testing when supported

**Priority**: High - Needed for optimal user experience

### Advanced Image Management
**Status**: Future consideration  
**Description**: Enhanced image organization and management features.

**Implementation Ideas**:
- Image tagging and categorization
- Bulk operations (delete, move, convert)
- Image metadata display (EXIF data, upload date, file size)
- Search and filtering capabilities

**Priority**: Low

## 🔄 System Features

### System Service Installation
**Status**: Planned - High Priority
**Description**: Install and uninstall scripts for running display controller as a Pi system service.

**Implementation Ideas**:
- Systemd service configuration and installation
- Auto-start on boot functionality  
- Service lifecycle management (start, stop, restart, status)
- Clean uninstall process with complete cleanup
- Service health monitoring and auto-recovery

**Priority**: High - Essential for production deployment

### Conversion Queue Management
**Status**: Future consideration
**Description**: Enhanced control over the image conversion process.

**Implementation Ideas**:
- Queue priority management
- Batch conversion controls
- Conversion progress tracking
- Failed conversion retry system

**Priority**: Medium

### Display Scheduling
**Status**: Future consideration
**Description**: Advanced scheduling and automation features.

**Implementation Ideas**:
- Time-based image rotation
- Weather-based image selection
- Holiday/event-based themes
- Remote control via API

**Priority**: Low

## 🌐 Integration Features

### Cloud Storage Integration
**Status**: Future consideration
**Description**: Support for additional cloud photo services.

**Implementation Ideas**:
- Dropbox integration
- OneDrive support
- iCloud Photos (where possible)
- Generic WebDAV support

**Priority**: Low

### Smart Home Integration
**Status**: Future consideration
**Description**: Integration with smart home platforms.

**Implementation Ideas**:
- Home Assistant integration
- MQTT support for IoT control
- Voice assistant integration
- Motion sensor triggered display changes

**Priority**: Low

## 🚀 Implementation Strategy

### Phase 1: Core Content Management (Next Sprint)
1. **Duplicate photo detection** - Complete implementation
2. **Google Photos image preview** - Add preview support
3. **Enhanced error handling** - Improve user feedback

### Phase 2: Advanced Management (Following Sprint)
1. **Conversion queue enhancements**
2. **Image metadata display**
3. **Bulk operations**

### Phase 3: Integration & Automation (Future)
1. **Additional cloud services**
2. **Smart home integration**
3. **Advanced scheduling**

## 📋 Development Notes

### Code Organization
- Keep features modular and optional
- Use feature flags for experimental functionality
- Maintain fallbacks for users without advanced features
- Document performance implications of new features

### Technical Constraints
- Maintain compatibility with existing ePaper display hardware
- Consider bandwidth limitations for cloud integrations
- Ensure features work reliably on Raspberry Pi hardware
- Keep memory usage reasonable for embedded systems