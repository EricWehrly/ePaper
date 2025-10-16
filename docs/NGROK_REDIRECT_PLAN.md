# Ngrok Redirect Banner Implementation Plan

## Overview
Implement a configurable countdown banner that redirects users from `raspberrypi.local` to the ngrok HTTPS URL for OAuth authentication. This provides better UX than immediate redirects while ensuring OAuth works correctly.

## Current State
- ✅ Google Photos OAuth integration complete
- ✅ Ngrok detection endpoint `/api/ngrok-info` working
- ✅ HTTPS redirect URI fix applied (uses ngrok URL for OAuth)
- ✅ Settings structure added to `config/settings.json` with ngrok_redirect config

## Configuration Added
```json
{
  "ngrok_redirect": {
    "enabled": true,
    "countdown_seconds": 7
  }
}
```

## Implementation Tasks

### 1. Backend Changes
- [ ] Update `/api/settings` endpoint to include ngrok_redirect config
- [ ] Ensure settings are loaded from `config/settings.json` on startup
- [ ] Test that `/api/settings` returns ngrok_redirect configuration

### 2. Frontend Detection Logic
- [ ] Add function to detect if user is on `raspberrypi.local` domain
- [ ] Fetch `/api/ngrok-info` to get current ngrok URL
- [ ] Fetch `/api/settings` to get redirect configuration
- [ ] Only show banner if:
  - User is on `raspberrypi.local` 
  - Ngrok is available and has HTTPS tunnel
  - `ngrok_redirect.enabled` is true
  - User is not already authenticated

### 3. Banner UI Implementation
- [ ] Create banner component in HTML/CSS:
  - Warning-style banner at top of page
  - Clear message about OAuth redirect requirement
  - Countdown timer display
  - Cancel and "Redirect Now" buttons
- [ ] Add CSS styling for banner (warning colors, fixed position)
- [ ] Implement JavaScript countdown logic:
  - Update countdown display every second
  - Auto-redirect when countdown reaches 0
  - Allow manual redirect via "Redirect Now" button
  - Allow cancellation (hide banner, set session flag)

### 4. JavaScript Implementation Details
```javascript
// Core functions needed:
- checkNgrokRedirectNeeded()
- showRedirectBanner(ngrokUrl, countdownSeconds)
- startCountdown(seconds, callback)
- redirectToNgrok(ngrokUrl)
- dismissBanner()
```

### 5. User Experience Flow
1. User visits `https://raspberrypi.local`
2. Page loads and checks if redirect needed
3. If needed, banner appears with message:
   ```
   "OAuth authentication requires HTTPS. Redirecting to secure tunnel in 7 seconds..."
   [Cancel] [Redirect Now] 
   Countdown: 6...5...4...3...2...1...
   ```
4. User can:
   - Wait for auto-redirect
   - Click "Redirect Now" for immediate redirect
   - Click "Cancel" to dismiss (won't show again this session)
5. After redirect, OAuth flow works normally
6. After OAuth success, user can return to `raspberrypi.local` normally

### 6. Banner Positioning Options
- **Option A**: Fixed banner at top of viewport (overlays content)
- **Option B**: Inline banner that pushes content down
- **Recommendation**: Option A for visibility, with semi-transparent backdrop

### 7. Session Handling
- [ ] Set session/localStorage flag when user cancels banner
- [ ] Don't show banner again during same session if dismissed
- [ ] Clear flag when user successfully authenticates

### 8. Configuration Testing
- [ ] Test with `ngrok_redirect.enabled: false` (no banner)
- [ ] Test with different countdown values (1s, 10s, etc.)
- [ ] Test banner behavior when ngrok is not available
- [ ] Test banner behavior when already authenticated

### 9. Error Handling
- [ ] Handle case where ngrok info fails to load
- [ ] Handle case where settings fail to load
- [ ] Graceful degradation if banner can't be shown

### 10. Technical Implementation Files
- **Backend**: `src/web/routes.py` (settings endpoint)
- **Frontend**: 
  - `src/web/static/index.html` (banner HTML)
  - `src/web/static/style.css` (banner styling)
  - `src/web/static/google_photos.js` or new `ngrok_banner.js`
- **Config**: `config/settings.json` (already updated)

## Testing Plan
1. **Local testing**: Access via `raspberrypi.local`, verify banner shows
2. **Ngrok testing**: Access via ngrok URL, verify banner doesn't show
3. **Config testing**: Toggle enabled flag, verify banner respects setting
4. **Countdown testing**: Verify countdown works and redirects properly
5. **Cancel testing**: Verify cancellation works and persists
6. **Auth testing**: Verify OAuth flow works after redirect

## Future Enhancements
- [ ] Add option to remember user preference (always/never redirect)
- [ ] Add different banner styles (info, warning, error)
- [ ] Add analytics/logging for redirect behavior
- [ ] Support for custom redirect messages per deployment

## Dependencies
- Existing ngrok detection endpoint (`/api/ngrok-info`)
- Settings endpoint that includes ngrok_redirect config
- Frontend JavaScript for DOM manipulation and timing
- CSS for banner styling and animations

## Risk Considerations
- Banner might be annoying if shown too frequently
- Countdown might be too fast/slow for some users
- Need to ensure banner doesn't interfere with existing UI
- Session state management for dismissed banners

## Success Criteria
- Users on `raspberrypi.local` can easily authenticate via ngrok
- Banner provides clear guidance without being intrusive
- Configuration allows disabling feature if needed
- No disruption to existing OAuth flow when accessed via ngrok directly