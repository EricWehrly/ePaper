# Drag-and-Drop Upload Feature Implementation Plan

## Overview
Add drag-and-drop file upload functionality to the ePaper web interface with conversion queuing system. Images dropped onto the interface will be uploaded, queued for conversion, and automatically displayed once ready.

---

## Phase 1: Essential Functionality (Test After This Phase)

### 1.1 Frontend: Drag-and-Drop UI
**Goal**: Add visual drop zone that appears when dragging supported files over the window.

**Tasks**:
- [ ] Add drag event listeners to `displayBox` element (dragenter, dragover, dragleave, drop)
- [ ] Create CSS styles for drop zone visual indicator (thick dashed border)
- [ ] Show drop zone overlay only when dragging supported image files (check file types in dragenter)
- [ ] Hide drop zone on dragleave (with proper event bubbling handling)
- [ ] Prevent default browser behavior for drag events

**Files to modify**:
- `src/web/static/app.js` - Add drag event handlers and drop zone logic
- `src/web/static/style.css` - Add drop zone visual styles
- `src/web/static/index.html` - May need minor markup adjustments

**Acceptance criteria**:
- Drop zone appears with dashed border when dragging image files over window
- Drop zone disappears when drag leaves or drop completes
- Non-image files don't trigger drop zone
- Browser's default drag behavior is prevented

---

### 1.2 Frontend: File Upload on Drop
**Goal**: Upload dropped files to the server.

**Tasks**:
- [ ] Implement drop event handler to capture dropped files
- [ ] Filter files to only supported extensions (.png, .jpg, .jpeg)
- [ ] Create FormData and upload files via POST to new `/api/upload` endpoint
- [ ] Show basic upload feedback (e.g., console log or simple status message)
- [ ] Handle upload errors gracefully

**Files to modify**:
- `src/web/static/app.js` - Add file upload logic to drop handler

**Acceptance criteria**:
- Dropped image files are uploaded to server
- Only supported image types are uploaded
- User sees indication that upload is in progress
- Errors are logged/displayed appropriately

---

### 1.3 Backend: Upload Endpoint
**Goal**: Accept uploaded files and save them to `pic-raw/` directory.

**Tasks**:
- [ ] Create `/api/upload` POST endpoint in routes
- [ ] Accept multipart/form-data file uploads
- [ ] Validate file types (only .png, .jpg, .jpeg)
- [ ] Save files to `pic-raw/` directory with safe filenames
- [ ] Return success response with uploaded file details

**Files to modify**:
- `src/web/routes.py` - Add upload endpoint

**Acceptance criteria**:
- Endpoint accepts file uploads
- Files are saved to `pic-raw/` with proper validation
- Duplicate filenames are handled (overwrite or rename)
- Response includes uploaded file paths

---

### 1.4 Backend: Conversion Queue System
**Goal**: Queue uploaded images for conversion and process them sequentially.

**Tasks**:
- [ ] Create conversion queue class/module to manage pending conversions
- [ ] Add images to queue when uploaded
- [ ] Process queue in background thread (one conversion at a time)
- [ ] Track conversion status (pending, in-progress, completed, failed)
- [ ] Create `/api/queue/status` endpoint to report queue state

**Files to create**:
- `src/convert/queue.py` - Queue management logic

**Files to modify**:
- `src/web/routes.py` - Add queue status endpoint
- `src/main.py` - Initialize conversion queue in controller

**Acceptance criteria**:
- Images are queued when uploaded
- Queue processes conversions sequentially
- Queue status is queryable via API
- Failed conversions are tracked and reported

---

### 1.5 Integration: Upload → Queue → Convert
**Goal**: Connect upload endpoint to conversion queue.

**Tasks**:
- [ ] Modify `/api/upload` to add uploaded files to conversion queue
- [ ] Queue starts processing automatically when files are added
- [ ] Queue status includes list of pending/in-progress/completed conversions
- [ ] Converted images appear in `pic/` directory when complete

**Files to modify**:
- `src/web/routes.py` - Connect upload to queue
- `src/main.py` - Ensure queue is running when web server starts

**Acceptance criteria**:
- Dropped files are automatically queued for conversion
- Conversions happen in background without blocking UI
- Converted images appear in output directory
- Multiple files can be queued and processed in order

---

### ✅ **TESTING CHECKPOINT 1**
**Test all essential functionality before proceeding to Phase 2**

**Test scenarios**:
1. Drag image file over window → drop zone appears
2. Drop image file → file uploads and enters queue
3. Queue processes conversion → converted image appears in `pic/`
4. Drop multiple files → all queue and convert in order
5. Error handling: invalid file type, upload failure, conversion failure

---

## Phase 2: Enhanced Features

### 2.1 Frontend: Queue UI with Thumbnails
**Goal**: Show queued/converting images in thumbnail area with status indicators.

**Tasks**:
- [ ] Poll `/api/queue/status` endpoint regularly (every 1-2 seconds)
- [ ] Display queued images in thumbnail area with special styling
- [ ] Show preview thumbnail for queued images (use source file preview)
- [ ] Add visual indicator for conversion status:
  - Pending: Queue icon/badge
  - In-progress: Spinner/progress indicator
  - Completed: Normal clickable thumbnail
  - Failed: Error indicator
- [ ] Disable click on thumbnails until conversion completes
- [ ] Auto-refresh converted images list when conversions complete

**Files to modify**:
- `src/web/static/app.js` - Add queue polling and thumbnail UI updates
- `src/web/static/style.css` - Add styling for queue status indicators
- `src/web/static/index.html` - May need markup for status badges

**Acceptance criteria**:
- Queued images appear in thumbnail area immediately after upload
- Status indicators clearly show pending/converting/completed states
- Thumbnails become clickable only after conversion completes
- UI updates automatically as conversions progress

---

### 2.2 Backend: Queue Persistence
**Goal**: Save queue state to disk so pending conversions resume after restart.

**Tasks**:
- [ ] Save queue state to `config/queue.json` when items are added/removed
- [ ] Load queue state on startup
- [ ] Compare `pic-raw/` against `pic/` to find unconverted images
- [ ] Add missing conversions to queue on startup
- [ ] Ensure queue processes persisted items automatically

**Files to modify**:
- `src/convert/queue.py` - Add persistence logic
- `src/main.py` - Load queue state on startup

**Acceptance criteria**:
- Queue state is saved to disk after changes
- Pending conversions resume when app restarts
- Images in `pic-raw/` without corresponding `pic/` entries are queued
- No duplicate queue entries after restart

---

### 2.3 Frontend: Enhanced Upload Feedback
**Goal**: Provide better visual feedback during upload and conversion.

**Tasks**:
- [ ] Show upload progress bar during file upload
- [ ] Display status message for each stage (uploading, queued, converting)
- [ ] Show success message when conversion completes
- [ ] Allow clicking completed thumbnail to display on ePaper immediately
- [ ] Add ability to cancel queued conversions (optional)

**Files to modify**:
- `src/web/static/app.js` - Enhanced upload UI and progress tracking
- `src/web/static/style.css` - Progress bar and message styling

**Acceptance criteria**:
- Upload progress is visible to user
- Status updates appear for each conversion stage
- User can interact with completed conversions
- UI is responsive and non-blocking

---

### 2.4 Backend: Queue Management Endpoints
**Goal**: Add API endpoints to manage the conversion queue.

**Tasks**:
- [ ] Create `/api/queue/clear` - Clear all pending items
- [ ] Create `/api/queue/remove/<id>` - Remove specific queue item
- [ ] Create `/api/queue/retry/<id>` - Retry failed conversion
- [ ] Update queue status endpoint to include detailed item info

**Files to modify**:
- `src/web/routes.py` - Add queue management endpoints
- `src/convert/queue.py` - Add management methods

**Acceptance criteria**:
- Queue can be cleared via API
- Individual items can be removed
- Failed conversions can be retried
- All endpoints return appropriate status codes

---

### 2.5 Polish: Edge Cases and Error Handling
**Goal**: Handle edge cases and improve robustness.

**Tasks**:
- [ ] Handle duplicate filenames (append number or timestamp)
- [ ] Limit maximum upload file size
- [ ] Validate image files are actual images (not renamed files)
- [ ] Handle disk full scenarios
- [ ] Add timeout for stuck conversions
- [ ] Show meaningful error messages to user
- [ ] Add logging for debugging queue issues

**Files to modify**:
- `src/web/routes.py` - Enhanced validation and error handling
- `src/convert/queue.py` - Timeout and failure recovery
- `src/web/static/app.js` - Better error display

**Acceptance criteria**:
- System handles all identified edge cases gracefully
- Users see clear error messages
- Logs provide sufficient debugging information
- No silent failures or undefined behavior

---

## Implementation Order Summary

### Must Complete (Phase 1):
1. Drag-and-drop UI with drop zone visual
2. File upload on drop
3. Backend upload endpoint
4. Conversion queue system
5. Integration: upload → queue → convert

### Can Add Later (Phase 2):
6. Queue UI with thumbnails and status indicators
7. Queue persistence and restart recovery
8. Enhanced upload feedback and progress
9. Queue management API endpoints
10. Edge case handling and polish

---

## Testing Strategy

### After Phase 1:
- Manual testing of basic drag-drop → upload → convert flow
- Test with single file
- Test with multiple files
- Test with invalid file types
- Test error scenarios (network failure, disk issues)

### After Phase 2:
- Test queue persistence across restarts
- Test thumbnail UI updates during conversion
- Test queue management operations
- Stress test with many files
- Test edge cases (duplicates, large files, etc.)

---

## Technical Notes

### File Structure
```
src/
├── web/
│   ├── routes.py          # Add upload & queue endpoints
│   └── static/
│       ├── app.js         # Add drag-drop & queue UI logic
│       ├── style.css      # Add drop zone styles
│       └── index.html     # Minor markup changes if needed
├── convert/
│   ├── queue.py           # NEW: Queue management logic
│   └── ...
└── main.py                # Initialize queue in controller
```

### API Endpoints to Add
- `POST /api/upload` - Upload files
- `GET /api/queue/status` - Get queue status
- `POST /api/queue/clear` - Clear queue (Phase 2)
- `DELETE /api/queue/remove/<id>` - Remove item (Phase 2)
- `POST /api/queue/retry/<id>` - Retry conversion (Phase 2)

### Queue Data Structure
```python
{
  "items": [
    {
      "id": "unique-id",
      "filename": "image.png",
      "source_path": "/path/to/pic-raw/image.png",
      "output_path": "/path/to/pic/image.bmp",
      "status": "pending|in-progress|completed|failed",
      "error": "error message if failed",
      "timestamp": 1234567890.0
    }
  ]
}
```

### Supported File Types
- `.png` - Portable Network Graphics
- `.jpg` / `.jpeg` - JPEG images

### Display Resolution
- Portrait: 400×600 pixels
- Landscape: 600×400 pixels
- 6-color palette: BLACK, WHITE, YELLOW, RED, BLUE, GREEN

---

## Success Criteria

### Phase 1 Success (Essential):
✅ User can drag-and-drop images onto the interface
✅ Images upload to server and save to `pic-raw/`
✅ Images queue for conversion automatically
✅ Queue processes conversions in background
✅ Converted images appear in `pic/` directory
✅ No blocking of main UI during conversions

### Phase 2 Success (Enhanced):
✅ Queue state persists across restarts
✅ Thumbnails show conversion status in real-time
✅ User receives clear feedback during all stages
✅ Edge cases handled gracefully
✅ Queue can be managed via UI/API

---

## Next Steps
1. Begin with Phase 1, Task 1.1 (Drag-and-Drop UI)
2. Complete each task in order
3. Test thoroughly after Phase 1 before starting Phase 2
4. Iterate on Phase 2 features as time permits
