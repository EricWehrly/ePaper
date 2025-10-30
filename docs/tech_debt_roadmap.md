# Tech Debt Roadmap

This document aggregates technical debt and improvement tasks across the ePaper Display codebase.

## 🔧 High Priority Technical Debt

### Display Module Cleanup
**Location**: `src/display/manager.py:66`
**Issue**: Late import of `waveshare_epd.epd4in0e` in function
**Impact**: Code organization and potential import issues
**TODO**: Move import to top of file where it belongs

### Toast Notification System
**Locations**: 
- `src/web/static/js/dragdrop.js:65` 
- `src/web/static/js/api.js:76`
**Issue**: Currently using `alert()` for user feedback
**Impact**: Poor user experience
**TODO**: Implement modern toast notification system

### Error Handling Improvements
**Locations**:
- `src/web/static/js/photo_upload.js:67`
- `src/web/static/js/dragdrop.js:70`
**Issue**: Missing user-friendly error messages and loading indicators
**Impact**: Poor user experience during uploads/conversions
**TODO**: Add loading spinners, progress indicators, and friendly error messages

## 🎯 Medium Priority Technical Debt

### Performance Optimization
**Location**: `src/convert/core.py:44`
**Issue**: Image conversion performance needs improvement
**Impact**: Slow conversion times, especially for batch operations
**TODO**: Profile and optimize conversion algorithm

### Photo Duplicate Detection
**Locations**:
- `src/web/static/js/photo_validation.js:39`
- `src/web/static/js/photo_upload.js:30`
**Issue**: Duplicate detection logic not implemented
**Impact**: Users can upload same photo multiple times
**TODO**: Implement file hash comparison and user confirmation dialogs

### Docker Volume Configuration
**Location**: `docker-compose.yml:1`
**Issue**: Picture directories not persisted across container restarts
**Impact**: Lost images when container is recreated
**TODO**: Configure volume mounts for pic/ and pic-raw/ directories

### Image Format Testing
**Locations**:
- `roadmap.md:5`
- `src/convert/batch.py:87-89`
**Issue**: Need conversion quality comparison between JPG/PNG
**Impact**: Unknown optimal source format for conversions
**TODO**: Set up visual comparison test infrastructure

## 🔄 Low Priority Technical Debt

### Display Configuration
**Location**: `src/main.py:95`
**Issue**: Hard-coded display cycle timing (22 vs 2 seconds)
**Impact**: No runtime configuration for different use cases
**TODO**: Make display timing configurable

### Image Orientation Handling
**Locations**:
- `src/main.py:220`
- `src/convert/preprocessing.py:60`
**Issue**: Orientation changes don't trigger reconversion
**Impact**: Images may display incorrectly after orientation changes
**TODO**: Implement automatic reconversion on orientation changes

### Server Configuration
**Location**: `src/web/server.py:32`
**Issue**: Unclear if current practice is optimal
**Impact**: Potential configuration or security concerns
**TODO**: Evaluate and document server configuration best practices

### Google Photos Album Support
**Location**: `src/web/static/js/google_photos_complex_backup.js:1145`
**Issue**: Album photo loading not implemented
**Impact**: Limited Google Photos integration
**TODO**: Implement album-based photo selection

### Installation Scripts
**Location**: `install.sh:3-5`
**Issue**: Installation and uninstallation scripts not implemented
**Impact**: Manual setup required for new users
**TODO**: Complete installation automation

### Display Cleanup
**Location**: `src/display/manager.py:250`
**Issue**: Additional cleanup code may be needed
**Impact**: Potential resource leaks or incomplete shutdown
**TODO**: Review and add any missing cleanup operations

## 🗂️ Code Organization Improvements

### Backup File Cleanup
**Location**: `src/web/static/js/google_photos_complex_backup.js`
**Issue**: Large backup file (1000+ lines) still in repository
**Impact**: Code clutter and confusion
**TODO**: Remove or relocate backup file after confirming current implementation works

### Documentation Consolidation
**Issue**: Multiple overlapping documentation files
**Impact**: Scattered and potentially conflicting information
**TODO**: Consolidate roadmap files into clear feature/interface/tech debt structure

## 🚀 Implementation Priority

### Sprint 1: User Experience (High Impact, Low Effort)
1. **Toast notification system** - Replace alerts with modern notifications
2. **Loading indicators** - Add spinners and progress bars
3. **Docker volume persistence** - Configure proper volume mounts

### Sprint 2: Core Functionality (High Impact, Medium Effort)
1. **Duplicate photo detection** - Implement hash-based comparison
2. **Performance optimization** - Profile and improve conversion speed
3. **Error handling improvements** - Better error messages and recovery

### Sprint 3: Configuration & Polish (Medium Impact, Various Effort)
1. **Display timing configuration** - Runtime configurable cycles
2. **Image orientation handling** - Auto-reconversion on changes
3. **Installation scripts** - Automated setup process

### Future: Advanced Features (Lower Priority)
1. **Google Photos albums** - Complete integration features
2. **Format comparison testing** - Optimize source formats
3. **Code organization** - Clean up backup files and improve structure

## 📋 Development Guidelines

### Code Quality Standards
- Move all imports to file tops where possible
- Implement proper error handling with user feedback
- Add loading states for all async operations
- Use modern JavaScript features (async/await over promises)
- Maintain backward compatibility with existing installations

### Performance Considerations
- Profile before optimizing
- Consider Raspberry Pi hardware constraints
- Batch operations where possible
- Implement caching for expensive operations

### User Experience Priorities
1. Clear feedback for all operations
2. Graceful error handling and recovery
3. Consistent visual design across interfaces
4. Responsive design for mobile access