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
  const dropZone = document.getElementById('playlistDropZone');
  if (!dropZone) return;

  let draggedImages = [];

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');

    const transferData = e.dataTransfer.getData('application/x-epaper-images');
    if (transferData) {
      try {
        draggedImages = JSON.parse(transferData);
        await createPlaylistFromImages(draggedImages);
      } catch (error) {
        console.error('Failed to parse dropped images:', error);
      }
    }
  });

  document.querySelectorAll('#thumbList .thumb img').forEach(img => {
    img.parentElement.setAttribute('draggable', 'true');
    
    img.parentElement.addEventListener('dragstart', (e) => {
      const imageSrc = img.getAttribute('src');
      const imageName = img.getAttribute('alt') || img.getAttribute('title');
      
      e.dataTransfer.effectAllowed = 'copy';
      e.dataTransfer.setData('application/x-epaper-images', JSON.stringify([imageName]));
    });
  });
}

/**
 * Create playlist from dropped images
 */
async function createPlaylistFromImages(imageNames) {
  if (!imageNames || imageNames.length === 0) {
    alert('No images to add to playlist');
    return;
  }

  const playlistName = prompt(`Create playlist with ${imageNames.length} images.\n\nEnter playlist name:`);
  if (!playlistName || !playlistName.trim()) {
    return;
  }

  try {
    const response = await apiPost('/api/playlists', {
      name: playlistName.trim(),
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