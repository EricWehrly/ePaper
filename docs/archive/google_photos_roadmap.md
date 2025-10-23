# Google Photos Integration Roadmap

## Overview

Phased implementation plan for integrating Google Photos Picker API with our e-paper display system. Each phase builds on the previous one, starting with the simplest possible integration.

---

## Phase 1: Basic Photo Selection & Download
*Goal: Single photo selection and display*  
*Timeline: 1-2 weeks*  
*Risk: Low*

### Deliverables
- [ ] Google Cloud Project setup with Photos Picker API enabled
- [ ] OAuth 2.0 credential configuration  
- [ ] Basic web route for starting photo selection
- [ ] Session creation and management
- [ ] Single photo download and save to `pic-raw/`
- [ ] Integration with existing conversion pipeline

### Technical Requirements
```python
# New API endpoints needed:
POST /api/google-photos/start-session    # Create picker session
GET  /api/google-photos/poll-session     # Check selection status  
POST /api/google-photos/download         # Download selected photos
```

### User Flow
1. User clicks "Select from Google Photos" button
2. App creates session, shows QR code + link
3. User opens Google Photos, selects ONE photo
4. App detects completion, downloads photo
5. Photo appears in conversion queue automatically

### Success Criteria
- User can successfully select a single photo from Google Photos
- Photo downloads to `pic-raw/` folder  
- Existing conversion system processes it normally
- Basic error handling for network issues

---

## Phase 2: Multiple Photo Selection
*Goal: Bulk photo selection and queuing*  
*Timeline: 1 week*  
*Risk: Low*

### Enhancements
- [ ] Support for multiple photo selection in single session
- [ ] Batch download with progress indication
- [ ] Queue management for multiple conversions
- [ ] User feedback during download process

### User Flow Updates
1. User selects multiple photos in Google Photos
2. App shows download progress (e.g., "3 of 7 photos downloaded")
3. All photos enter conversion queue
4. User can start new session for more photos

### Technical Additions
```python
# Enhanced functionality:
- Pagination handling for large selections
- Concurrent downloads (rate limited)
- Progress websocket updates
- Batch processing integration
```

---

## Phase 3: Enhanced UX & Error Handling
*Goal: Production-ready user experience*  
*Timeline: 1-2 weeks*  
*Risk: Medium*

### Improvements
- [ ] Better visual feedback (progress bars, previews)
- [ ] Comprehensive error handling and recovery
- [ ] Session timeout management
- [ ] User education/onboarding flow
- [ ] Mobile-optimized interface

### User Experience Enhancements
- **Onboarding**: Step-by-step guide for first-time users
- **Preview Mode**: Show thumbnails of selected photos before download
- **Error Recovery**: Clear messages and retry options
- **Cross-Device**: Optimized for phone selection → tablet display

### Technical Robustness
```python
# Error scenarios to handle:
- Network connectivity issues
- OAuth token expiration  
- API rate limit exceeded
- Invalid/expired download URLs
- Partial download failures
- Large file timeouts
```

---

## Phase 4: Batch Processing & Smart Selection
*Goal: Semi-automated photo curation*  
*Timeline: 2-3 weeks*  
*Risk: Medium-High*

### Feature Additions
- [ ] Batch photo scoring after user selection
- [ ] "Smart selection" recommendations from user-selected batches
- [ ] Album-guided selection workflows  
- [ ] Scheduled re-selection reminders
- [ ] Integration with photo scoring system

### Semi-Automated Capabilities
- **Batch Score & Filter**: User selects 50+ photos, app scores all and shows top candidates
- **Smart Recommendations**: "Your top 10 photos from this selection based on e-paper suitability"  
- **Album Shortcuts**: Save frequently accessed album search terms
- **Scoring Integration**: Full integration with existing color/edge/skin detection scoring
- **Selection Memory**: Remember user's preferences from past selections

### Technical Complexity
```python
# New systems needed:
- User preferences storage
- Background task scheduling
- Advanced photo metadata parsing
- Integration with existing scoring system
```

---

## Phase 5: Integration Polish
*Goal: Seamless ecosystem integration*  
*Timeline: 1-2 weeks*  
*Risk: Low*

### Final Integrations
- [ ] Unified photo source selection (local + Google Photos)
- [ ] Settings panel integration
- [ ] Performance optimization
- [ ] Documentation and user guides
- [ ] Testing and validation

### System Integration
- **Unified Interface**: Single "Add Photos" button that offers both local and Google Photos
- **Settings Integration**: Google Photos preferences in main settings
- **Performance**: Caching, lazy loading, optimized downloads
- **Monitoring**: Usage analytics, error tracking

---

## Automated Workflow Alternatives

Since full library trawling is not possible, here are realistic approaches that achieve similar goals:

### 1. Batch Selection + Auto-Scoring 🎯 **(Recommended)**
**User Flow**:
1. User selects large batch (20-100 photos) from Google Photos
2. App downloads and runs scoring algorithm on all photos
3. App presents top-scored photos: "Here are your 5 best e-paper candidates"
4. User can accept recommendations or review full results

**Benefits**: 
- Leverages your scoring system
- User maintains control
- Works within API constraints
- Can process hundreds of photos efficiently

### 2. Album-Based Curation 📂
**User Flow**:
1. User creates Google Photos albums for different themes (vacations, portraits, etc.)
2. App guides user to select from specific albums
3. App processes entire album selection and ranks by e-paper suitability
4. Regular "refresh" sessions to check for new photos in favorite albums

**Benefits**:
- Organized by user's existing photo management
- Can establish patterns (user likes vacation photos best for e-paper)
- Natural way to categorize and revisit photo sets

### 3. Periodic "Curation Sessions" 🔄
**User Flow**:
1. App suggests weekly/monthly "photo curation" sessions
2. User selects from recent photos (last month, season, etc.)
3. App scores and maintains a "best of" collection
4. Can build up a curated library over time

**Benefits**:
- Feels automated from user perspective
- Builds comprehensive scoring data
- Can learn user preferences over time

### 4. Smart Recommendations Engine 🧠
**Enhancement to any above**:
- Track which high-scored photos user actually displays
- Learn user's preferences beyond just technical scores
- Provide better recommendations: "Photos like the ones you usually choose"
- Build personalized e-paper photo profiles

---

## Implementation Details

### Phase 1 Technical Setup

#### 1. Google Cloud Configuration
```bash
# Enable required APIs
gcloud services enable photoslibrary.googleapis.com
gcloud services enable photospicker.googleapis.com

# Create OAuth credentials
# - Application type: Web application  
# - Authorized redirect URIs: http://localhost:5000/oauth/callback
# - Scopes: https://www.googleapis.com/auth/photospicker.mediaitems.readonly
```

#### 2. Dependencies
```python
# Add to requirements.txt
google-auth==2.23.0
google-auth-oauthlib==1.1.0
requests==2.31.0
```

#### 3. Basic Flask Routes
```python
# src/web/routes.py additions
@app.route('/api/google-photos/start-session', methods=['POST'])
def start_google_photos_session():
    # Create picker session
    # Return session ID and picker URI
    pass

@app.route('/api/google-photos/poll/<session_id>')  
def poll_session(session_id):
    # Check if user has completed selection
    # Return status and media items if ready
    pass
```

#### 4. Frontend Integration
```javascript
// Add to existing web interface
function startGooglePhotosSelection() {
    fetch('/api/google-photos/start-session', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            showPickerInterface(data.picker_uri, data.session_id);
        });
}
```

### File Structure Changes
```
src/
├── google_photos/
│   ├── __init__.py
│   ├── auth.py          # OAuth 2.0 handling
│   ├── picker.py        # Picker API interface  
│   ├── downloader.py    # Photo download logic
│   └── session.py       # Session management
├── web/
│   ├── static/
│   │   └── google-photos.js   # Frontend interactions
│   └── templates/
│       └── google-photos-picker.html
```

---

## Risk Mitigation

### Technical Risks
1. **API Rate Limits**
   - Implement exponential backoff
   - Add request queuing system
   - Monitor usage dashboard

2. **OAuth Complexity**  
   - Use well-tested libraries (google-auth-oauthlib)
   - Implement robust token refresh
   - Clear error messages for auth failures

3. **Network Reliability**
   - Retry logic for failed downloads
   - Partial download recovery
   - Offline mode graceful degradation

### User Experience Risks
1. **Flow Confusion**
   - Create clear onboarding tutorial
   - Visual guides for QR code scanning
   - Fallback to local upload always available

2. **Mobile/Desktop Coordination**
   - Test cross-device flows extensively
   - Provide both QR and direct link options
   - Clear instructions for each platform

---

## Success Metrics

### Phase 1
- [ ] Successful photo selection in <30 seconds
- [ ] 100% download success rate for selected photos  
- [ ] Zero crashes during selection flow

### Phase 2-3
- [ ] Support for 10+ photos in single session
- [ ] <5% user error rate in selection flow
- [ ] Error recovery success rate >90%

### Phase 4-5
- [ ] User retention >80% after first use
- [ ] Average session time <2 minutes
- [ ] Performance metrics meet existing app standards

---

## Alternative Scenarios

### Fallback Plans
1. **If API limits become restrictive**: Implement user quotas and premium tiers
2. **If OAuth verification fails**: Provide detailed setup instructions for personal use
3. **If user adoption low**: Maintain as optional feature alongside local upload

### Future Considerations
1. **Other Cloud Providers**: Similar integration with iCloud, Dropbox if successful
2. **AI Integration**: Auto-selection based on photo scoring system
3. **Social Features**: Share favorite photo selections with other users

---

*This roadmap prioritizes quick wins and iterative improvement to minimize risk while building toward a comprehensive Google Photos integration.*