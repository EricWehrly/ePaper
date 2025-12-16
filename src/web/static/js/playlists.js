/**
 * Playlist management functionality for ePaper interface
 */

import { getElement } from './dom.js';
import { apiGet, apiPost } from './api.js';

// Track current preview playlist for click-to-play functionality
let currentPreviewPlaylistId = null;

/**
 * Initialize playlist functionality
 */
export function initializePlaylists() {
  console.log('Initializing playlists module');
  
  // Note: Tab switching is now handled by tab_switcher.js
  // We no longer need setupTabSwitching() here
  
  // Setup display area tabs
  setupDisplayTabs();
  
  // Setup event handlers
  setupPlaylistEventHandlers();
  
  console.log('Playlists module initialized');
}

/**
 * Setup tab switching between Thumbs and Playlists
 * NOTE: Tab switching is now handled by tab_switcher.js
 * This function is kept for backwards compatibility but does nothing
 */
function setupTabSwitching() {
  // Tab switching is now handled by tab_switcher.js
  console.log('Tab switching handled by tab_switcher.js');
}

/**
 * Switch to the specified tab
 * @param {string} tabName - Name of tab to switch to ('thumbs' or 'playlists')
 * NOTE: This is now handled by tab_switcher.js
 */
function switchTab(tabName) {
  // Tab switching is now handled by tab_switcher.js
  // Trigger click on the appropriate tab button to use the centralized handler
  const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);
  if (tabBtn) {
    tabBtn.click();
  }
}

/**
 * Setup display area tabs (Display/Preview)
 */
function setupDisplayTabs() {
  const displayTabBtn = document.getElementById('displayTabBtn');
  const previewTabBtn = document.getElementById('previewTabBtn');
  const displayTabPane = document.getElementById('displayTabPane');
  const previewTabPane = document.getElementById('previewTabPane');

  if (!displayTabBtn || !previewTabBtn || !displayTabPane || !previewTabPane) {
    console.warn('Display tab elements not found');
    return;
  }

  // Display tab button click
  displayTabBtn.addEventListener('click', () => {
    switchDisplayTab('display');
  });

  // Preview tab button click
  previewTabBtn.addEventListener('click', () => {
    switchDisplayTab('preview');
  });
}

/**
 * Switch display area tab
 * @param {string} tabName - Name of tab to switch to ('display' or 'preview')
 */
function switchDisplayTab(tabName) {
  // Update button states
  document.querySelectorAll('.display-tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

  // Update tab content visibility
  document.querySelectorAll('.display-tab-pane').forEach(pane => {
    pane.classList.remove('active');
  });
  document.getElementById(`${tabName}TabPane`).classList.add('active');

  console.log(`Switched to ${tabName} display tab`);
}

/**
 * Load playlists from server
 */
async function loadPlaylists() {
  try {
    const response = await apiGet('/api/playlists');
    if (response.playlists) {
      // Transform server data to match UI expectations
      const playlists = response.playlists.map(playlist => ({
        id: playlist.id,
        name: playlist.name || 'Untitled Playlist',
        imageCount: playlist.images ? playlist.images.length : 0,
        delay: playlist.delay || 5000
      }));
      
      renderPlaylists(playlists);
    } else {
      console.warn('No playlists found');
      renderPlaylists([]);
    }
  } catch (error) {
    console.error('Failed to load playlists:', error);
    // Fallback to mock data for development
    const mockPlaylists = [
      { id: 'morning', name: 'Morning Slideshow', imageCount: 4, delay: 10000 },
      { id: 'tech', name: 'Tech Gallery', imageCount: 6, delay: 15000 },
      { id: 'quick', name: 'Quick Rotation', imageCount: 2, delay: 3000 }
    ];
    renderPlaylists(mockPlaylists);
  }
}

/**
 * Render playlist list
 * @param {Array} playlists - Array of playlist objects
 */
function renderPlaylists(playlists) {
  const playlistList = document.getElementById('playlistList');
  if (!playlistList) return;

  playlistList.innerHTML = '';

  playlists.forEach(playlist => {
    const playlistItem = document.createElement('div');
    playlistItem.className = 'playlist-item';
    playlistItem.innerHTML = `
      <div class="playlist-info">
        <div class="playlist-name">${playlist.name}</div>
        <div class="playlist-count">${playlist.imageCount} images • ${playlist.delay/1000}s delay</div>
      </div>
      <div class="playlist-actions">
        <button class="ctl-btn control primary small" data-playlist-id="${playlist.id}">Play</button>
        <button class="ctl-btn control small" data-playlist-id="${playlist.id}" data-action="preview">Preview</button>
      </div>
    `;

    // Add event listeners
    const playBtn = playlistItem.querySelector('[data-action="play"]') || playlistItem.querySelector('[data-playlist-id]:not([data-action])');
    const previewBtn = playlistItem.querySelector('[data-action="preview"]');

    if (playBtn) {
      playBtn.addEventListener('click', () => playPlaylist(playlist.id));
    }

    if (previewBtn) {
      previewBtn.addEventListener('click', () => showPlaylistPreview(playlist.id));
    }

    playlistList.appendChild(playlistItem);
  });
}

/**
 * Play a playlist
 * @param {string} playlistId - ID of playlist to play
 * @param {number} startIndex - Optional starting index (default: 0)
 */
async function playPlaylist(playlistId, startIndex = 0) {
  try {
    console.log(`Starting playlist: ${playlistId} at index ${startIndex}`);
    
    // Call backend API to start playlist
    const response = await apiPost(`/api/playlists/${playlistId}/play`, {
      start_index: startIndex
    });
    
    if (response.success) {
      console.log(`Playlist ${playlistId} started successfully`);
      
      // Update current playlist display
      const currentPlaylistName = document.getElementById('currentPlaylistName');
      if (currentPlaylistName) {
        currentPlaylistName.textContent = response.playlist_id || playlistId;
      }
      
      // Show success message (could add toast notification here)
      console.log('Playlist playback started');
    } else {
      throw new Error(response.error || 'Unknown error starting playlist');
    }
  } catch (error) {
    console.error('Failed to play playlist:', error);
    // Could show error toast notification here
    alert(`Failed to start playlist: ${error.message}`);
  }
}

/**
 * Show playlist preview
 * @param {string} playlistId - ID of playlist to preview
 */
async function showPlaylistPreview(playlistId) {
  try {
    console.log(`Previewing playlist: ${playlistId}`);
    
    // Switch to preview tab
    switchDisplayTab('preview');
    
    // Track current preview playlist
    currentPreviewPlaylistId = playlistId;
    
    // Load actual playlist data from API
    const playlist = await apiGet(`/api/playlists/${playlistId}`);
    
    if (playlist && playlist.images) {
      renderPreviewImages(playlist.images);
    } else {
      // Fallback to mock data
      const mockImages = ['image1.bmp', 'image2.bmp', 'image3.bmp', 'image4.bmp'];
      renderPreviewImages(mockImages);
    }
  } catch (error) {
    console.error('Failed to load playlist preview:', error);
    // Fallback to mock data
    const mockImages = ['image1.bmp', 'image2.bmp', 'image3.bmp', 'image4.bmp'];
    renderPreviewImages(mockImages);
  }
}

/**
 * Render preview images
 * @param {Array} images - Array of image filenames
 */
function renderPreviewImages(images) {
  const previewImages = document.getElementById('previewImages');
  const previewPlaceholder = document.querySelector('.preview-placeholder');
  
  if (!previewImages) return;

  // Hide placeholder, show images
  if (previewPlaceholder) previewPlaceholder.style.display = 'none';
  
  previewImages.innerHTML = '';
  previewImages.style.display = 'grid';

  images.forEach((image, index) => {
    const imageDiv = document.createElement('div');
    imageDiv.className = 'preview-image';
    imageDiv.innerHTML = `
      <img src="/static_image?path=pic/${image}" alt="${image}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0yMCAzMEMyNS41MjI5IDMwIDMwIDI1LjUyMjkgMzAgMjBDMzAgMTQuNDc3MSAyNS41MjI5IDEwIDIwIDEwQzE0LjQ3NzEgMTAgMTAgMTQuNDc3MSAxMCAyMEMxMCAyNS41MjI5IDE0LjQ3NzEgMzAgMjAgMzBaIiBzdHJva2U9IiM5Q0EzQUYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+CjxwYXRoIGQ9Ik0xNC41IDE0LjVMMjUuNSAyNS41IiBzdHJva2U9IiM5Q0EzQUYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+CjxwYXRoIGQ9Ik0yNS41IDE0LjVMMTQuNSAyNS41IiBzdHJva2U9IiM5Q0EzQUYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+Cjwvc3ZnPgo='">
      <div class="image-index">${index + 1}</div>
    `;

    // Add click handler to start playlist at this index
    imageDiv.addEventListener('click', () => {
      console.log(`Starting playlist at index ${index}`);
      // Use tracked preview playlist ID
      if (currentPreviewPlaylistId) {
        playPlaylist(currentPreviewPlaylistId, index);
      }
    });

    previewImages.appendChild(imageDiv);
  });
}

/**
 * Stop current playlist playback
 */
async function stopCurrentPlaylist() {
  try {
    console.log('Stopping current playlist');
    
    const response = await apiPost('/api/playlists/stop');
    
    if (response.success) {
      console.log('Playlist stopped successfully');
      
      // Clear current playlist display
      const currentPlaylistName = document.getElementById('currentPlaylistName');
      if (currentPlaylistName) {
        currentPlaylistName.textContent = 'None';
      }
    } else {
      throw new Error(response.error || 'Unknown error stopping playlist');
    }
  } catch (error) {
    console.error('Failed to stop playlist:', error);
    alert(`Failed to stop playlist: ${error.message}`);
  }
}

/**
 * Setup drag and drop for playlist creation
 */
function setupPlaylistDragDrop() {
  // TODO: Make a proper drop zone that appears on drag instead of using whole document
  
  let dragCounter = 0;

  // Show visual feedback when dragging files into window
  document.addEventListener('dragenter', (e) => {
    if (e.dataTransfer.types && e.dataTransfer.types.includes('Files')) {
      dragCounter++;
      document.body.classList.add('dragging-files');
    }
  });

  document.addEventListener('dragleave', (e) => {
    if (e.dataTransfer.types && e.dataTransfer.types.includes('Files')) {
      dragCounter--;
      if (dragCounter === 0) {
        document.body.classList.remove('dragging-files');
      }
    }
  });

  // Prevent default drag behavior on document
  document.addEventListener('dragover', (e) => {
    if (e.dataTransfer.types && e.dataTransfer.types.includes('Files')) {
      e.preventDefault();
    }
  });

  // Handle drops anywhere on the document
  document.addEventListener('drop', async (e) => {
    // Handle file drops from OS
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      e.preventDefault();
      dragCounter = 0;
      document.body.classList.remove('dragging-files');
      await handleFileDrop(e.dataTransfer.files);
    }
  });
}

/**
 * Upload a batch of files
 * @param {File[]} files - Array of files to upload
 * @returns {Promise<Object>} Upload result
 */
async function uploadBatch(files) {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData
  });

  console.log('Upload response status:', response.status, response.statusText);

  if (!response.ok) {
    const text = await response.text();
    console.error('Upload failed response:', text.substring(0, 500));
    
    // Provide helpful error messages
    if (response.status === 413) {
      const error = new Error(`Upload too large (nginx limit reached)`);
      error.status = 413;
      throw error;
    } else if (response.status === 500 && (text.includes('<!DOCTYPE') || text.includes('<html'))) {
      throw new Error(`Server error. Check console for details. Status: ${response.status}`);
    } else {
      throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
    }
  }

  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('application/json')) {
    const text = await response.text();
    console.error('Received non-JSON response:', text.substring(0, 500));
    throw new Error(`Server returned HTML instead of JSON. This usually means an error occurred. Check console for details.`);
  }

  const result = await response.json();
  
  if (!result.success) {
    throw new Error(result.error || 'Upload failed');
  }
  
  return result;
}

/**
 * Handle files dropped from OS
 */
async function handleFileDrop(files) {
  // Filter for image files - include all image types
  const imageFiles = Array.from(files).filter(file => 
    file.type.startsWith('image/') || 
    file.name.toLowerCase().match(/\.(jpg|jpeg|png|gif|bmp|webp|heic|heif)$/)
  );

  if (imageFiles.length === 0) {
    const msg = 'Please drop image files';
    console.warn('ALERT:', msg);
    alert(msg);
    return;
  }

  try {
    console.log('Uploading files:', imageFiles.map(f => `${f.name} (${(f.size / 1024 / 1024).toFixed(2)}MB)`));
    
    // TODO: Implement client-side zip compression for efficient multi-image upload
    // This would compress images into a zip file before sending, reducing network transfer
    // and allowing more images per upload while staying under size limits
    
    // Get max upload size from settings
    const settingsResponse = await fetch('/api/settings');
    const settings = await settingsResponse.json();
    const maxUploadSize = settings.max_upload_size || (200 * 1024 * 1024); // 200MB default
    
    console.log('Max upload size:', (maxUploadSize / 1024 / 1024).toFixed(1), 'MB');
    
    // Batch files to stay under max upload size (with 20% safety margin)
    const safeMaxSize = maxUploadSize * 0.8;
    const batches = [];
    let currentBatch = [];
    let currentBatchSize = 0;
    
    for (const file of imageFiles) {
      // If single file is too large, skip it
      if (file.size > safeMaxSize) {
        const msg = `File "${file.name}" is too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max size is ${(safeMaxSize / 1024 / 1024).toFixed(1)}MB`;
        console.warn('ALERT:', msg);
        alert(msg);
        continue;
      }
      
      // If adding this file would exceed batch size, start new batch
      if (currentBatchSize + file.size > safeMaxSize && currentBatch.length > 0) {
        batches.push(currentBatch);
        currentBatch = [];
        currentBatchSize = 0;
      }
      
      currentBatch.push(file);
      currentBatchSize += file.size;
    }
    
    // Add final batch
    if (currentBatch.length > 0) {
      batches.push(currentBatch);
    }
    
    if (batches.length === 0) {
      const msg = 'No valid files to upload';
      console.warn('ALERT:', msg);
      alert(msg);
      return;
    }
    
    console.log(`Uploading ${imageFiles.length} files in ${batches.length} batch(es)`);
    
    // Upload batches sequentially
    const allUploadedNames = [];
    let failedBatch = null;
    
    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      const batchSize = batch.reduce((sum, f) => sum + f.size, 0);
      console.log(`Uploading batch ${i + 1}/${batches.length} (${batch.length} files, ${(batchSize / 1024 / 1024).toFixed(2)}MB)`);
      
      try {
        const result = await uploadBatch(batch);
        
        // Collect uploaded filenames (without extensions for playlist)
        const uploadedNames = result.uploaded_files.map(f => {
          const name = f.filename;
          return name.substring(0, name.lastIndexOf('.')) || name;
        });
        
        allUploadedNames.push(...uploadedNames);
      } catch (error) {
        // If batch upload fails with 413, try uploading files one at a time
        if (error.status === 413 && batch.length > 1) {
          console.warn(`Batch ${i + 1} too large (${(batchSize / 1024 / 1024).toFixed(2)}MB), falling back to one-at-a-time upload`);
          
          for (let j = 0; j < batch.length; j++) {
            const file = batch[j];
            console.log(`  Uploading file ${j + 1}/${batch.length}: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
            
            try {
              const result = await uploadBatch([file]);
              const uploadedNames = result.uploaded_files.map(f => {
                const name = f.filename;
                return name.substring(0, name.lastIndexOf('.')) || name;
              });
              allUploadedNames.push(...uploadedNames);
            } catch (singleError) {
              console.error(`Failed to upload ${file.name}:`, singleError);
              // Continue with other files
            }
          }
        } else {
          // For other errors or single-file failures, record and continue
          console.error(`Batch ${i + 1} failed:`, error);
          failedBatch = error;
        }
      }
    }

    // Check if we have files to create playlist from
    if (allUploadedNames.length === 0) {
      if (failedBatch) {
        const msg = `Upload failed: ${failedBatch.message}\n\nNote: If you see "413 Payload Too Large" from nginx, the server administrator needs to increase nginx's client_max_body_size setting.`;
        console.error('ALERT:', msg);
        alert(msg);
        return;
      }
      
      // If all files were skipped (already converted), still create playlist with them
      console.log('All files already converted, creating playlist from existing files');
      
      // Get base names from the original dropped files
      const existingImageNames = imageFiles.map(f => {
        const name = f.name;
        return name.substring(0, name.lastIndexOf('.')) || name;
      });
      
      if (existingImageNames.length > 0) {
        await createPlaylistFromImages(existingImageNames);
        return;
      }
      
      const msg = 'No files to create playlist from';
      console.warn('ALERT:', msg);
      alert(msg);
      return;
    }

    console.log(`Successfully uploaded ${allUploadedNames.length} files`);

    // Wait a moment for conversion to complete
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Create playlist from uploaded images
    await createPlaylistFromImages(allUploadedNames);
    
  } catch (error) {
    console.error('Failed to handle file drop:', error);
    let errorMessage = `Failed to upload files: ${error.message}`;
    if (error.status === 413) {
      errorMessage += '\n\nNote: nginx is blocking large uploads. Server admin needs to add:\nclient_max_body_size 200M;\nto nginx configuration.';
    }
    console.error('ALERT:', errorMessage);
    alert(errorMessage);
  }
}

/**
 * Create playlist from dropped images
 */
async function createPlaylistFromImages(imageNames) {
  if (!imageNames || imageNames.length === 0) {
    alert('No images to add to playlist');
    return;
  }

  // Show the prompt UI at the bottom
  const promptElement = document.getElementById('playlistNamePrompt');
  const inputElement = document.getElementById('playlistNameInput');
  const createBtn = document.getElementById('createPlaylistBtn');
  const cancelBtn = document.getElementById('cancelPlaylistBtn');

  if (!promptElement || !inputElement || !createBtn || !cancelBtn) {
    // Fallback to browser prompt if elements not found
    const playlistName = prompt(`Create playlist with ${imageNames.length} images.\n\nEnter playlist name:`);
    if (!playlistName || !playlistName.trim()) {
      return;
    }
    await submitPlaylistCreation(playlistName.trim(), imageNames);
    return;
  }

  // Show prompt and focus input
  promptElement.style.display = 'flex';
  inputElement.value = '';
  inputElement.placeholder = `Create playlist with ${imageNames.length} images...`;
  inputElement.focus();

  // Handle create button
  const handleCreate = async () => {
    const playlistName = inputElement.value.trim();
    if (!playlistName) {
      inputElement.focus();
      return;
    }
    cleanup();
    await submitPlaylistCreation(playlistName, imageNames);
  };

  // Handle cancel button
  const handleCancel = () => {
    cleanup();
  };

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleCreate();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  // Cleanup function
  const cleanup = () => {
    promptElement.style.display = 'none';
    createBtn.removeEventListener('click', handleCreate);
    cancelBtn.removeEventListener('click', handleCancel);
    inputElement.removeEventListener('keypress', handleKeyPress);
  };

  // Attach event listeners
  createBtn.addEventListener('click', handleCreate);
  cancelBtn.addEventListener('click', handleCancel);
  inputElement.addEventListener('keypress', handleKeyPress);
}

/**
 * Submit playlist creation to server
 */
async function submitPlaylistCreation(playlistName, imageNames) {
  try {
    const response = await apiPost('/api/playlists', {
      name: playlistName,
      images: imageNames,
      interval: 30,
      orientation: 'portrait'
    });

    if (response.success) {
      alert(`Playlist "${playlistName}" created successfully!`);
      loadPlaylists();
    } else {
      throw new Error(response.error || 'Failed to create playlist');
    }
  } catch (error) {
    console.error('Failed to create playlist:', error);
    alert(`Failed to create playlist: ${error.message}`);
  }
}

/**
 * Setup playlist event handlers
 */
function setupPlaylistEventHandlers() {
  loadPlaylists();
  setupPlaylistDragDrop();

  const stopBtn = document.getElementById('stopPlaylist');
  if (stopBtn) {
    stopBtn.addEventListener('click', () => stopCurrentPlaylist());
  }

  const clearPreviewBtn = document.getElementById('clearPreview');
  if (clearPreviewBtn) {
    clearPreviewBtn.addEventListener('click', () => {
      const previewImages = document.getElementById('previewImages');
      const previewPlaceholder = document.querySelector('.preview-placeholder');
      
      if (previewImages) {
        previewImages.innerHTML = '';
        previewImages.style.display = 'none';
      }
      
      if (previewPlaceholder) {
        previewPlaceholder.style.display = 'flex';
      }
    });
  }

  console.log('Playlist event handlers setup complete');
}

/**
 * Get current active tab
 * @returns {string} - Active tab name
 */
export function getActiveTab() {
  const activeTabBtn = document.querySelector('.tab-btn.active');
  return activeTabBtn?.dataset.tab || 'thumbs';
}

/**
 * Check if playlists tab is currently active
 * @returns {boolean}
 */
export function isPlaylistsTabActive() {
  return getActiveTab() === 'playlists';
}