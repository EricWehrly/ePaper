/**
 * UI refresh and update logic
 */

import { el } from './utils.js';
import { state, updateState } from './state.js';
import { setBusyState, displayImage } from './display.js';
import { apiGet, API_CONFIG } from './api.js';
import { getElement, setText, setAttribute, setVisible, toggleClass } from './dom.js';

/**
 * Refresh status from server and update UI
 */
export async function refresh() {
  try {
    const status = await apiGet(API_CONFIG.ENDPOINTS.STATUS);
    
    // Update current image display
    const current = status.current_image || null;
    const imgEl = getElement('CURRENT_IMAGE');
    if (current && imgEl) {
      imgEl.src = '/static_image?path=' + encodeURIComponent(current);
      setVisible('CURRENT_IMAGE', true);
      setVisible('PLACEHOLDER', false);
    } else {
      if (imgEl) imgEl.src = '';
      setVisible('CURRENT_IMAGE', false);
      setVisible('PLACEHOLDER', true);
    }

    // Check if image counts have changed
    const previousCounts = state.imageCounts;
    const newCounts = status.image_counts || { source: 0, converted: 0 };
    const countsChanged = (
      previousCounts.source !== newCounts.source || 
      previousCounts.converted !== newCounts.converted
    );

    // Update state from status (but store previous busy state first)
    const previousBusyState = state.busy;
    updateState({
      settings: status.settings || state.settings,
      busy: status.busy,
      carouselActive: status.carousel_active || false,
      imageCounts: newCounts
    });
    
    // Auto-refresh images if counts changed
    if (countsChanged) {
      console.log(`📊 Image count changed: ${previousCounts.converted} → ${newCounts.converted} converted images`);
      setTimeout(refreshImages, 100);
    }
    
    // Update UI controls based on status
    updateControlsFromStatus(status, previousBusyState);
  } catch (e) {
    console.error(e);
  }
  return Promise.resolve(); // Ensure it returns a promise
}

/**
 * Refresh images list from server
 */
export async function refreshImages() {
  try {
    const images = await apiGet(API_CONFIG.ENDPOINTS.IMAGES);
    const list = getElement('THUMBS_LIST');
    
    if (!list) {
      console.error('❌ Failed to find #thumbList element - thumbnails cannot be rendered');
      return;
    }
    
    console.log('✓ Found #thumbList element, rendering thumbnails...');
    
    // Only show converted images for now
    const all = images.converted_images || [];
    updateState({ convertedImages: all });
    
    // Images are now pre-sorted by creation time (newest first) from backend
    console.log('Current thumbnail ordering: newest first by creation time');
    
    // Identify completed conversions and remove their placeholders (robust matching)
    const convertedFilenames = all.map(img => img.name.replace(/\.bmp$/, ''));
    const completedConversions = [];
    
    state.pendingUploads.forEach(pending => {
      // Try multiple matching strategies for robust detection
      const originalName = pending.filename;
      const baseFilename = originalName.replace(/\.(png|jpg|jpeg|gif|webp|bmp)$/i, '');
      
      // Check if any converted image matches this pending upload
      const isConverted = convertedFilenames.some(converted => {
        // Exact base name match
        if (converted === baseFilename) return true;
        // Handle potential filename cleaning/sanitization
        const cleanOriginal = baseFilename.replace(/[^\w\-_]/g, '_');
        const cleanConverted = converted.replace(/[^\w\-_]/g, '_');
        return cleanOriginal === cleanConverted;
      });
      
      if (isConverted) {
        completedConversions.push(originalName);
        removePendingUploadPlaceholder(originalName);
      }
    });
    
    // Get existing thumbnails to avoid flashing during rebuild
    const existingThumbnails = Array.from(list.children);
    const existingImagePaths = existingThumbnails
      .filter(thumb => thumb.querySelector('img'))
      .map(thumb => thumb.querySelector('img').getAttribute('src'));
    
    // Only rebuild if the order has significantly changed, otherwise just add new items
    const shouldFullRebuild = existingThumbnails.length === 0 || completedConversions.length > 0;
    
    if (shouldFullRebuild) {
      // Clear and rebuild (only when necessary)
      list.innerHTML = '';
      
      // Add placeholder thumbnails first (newest on top)
      state.pendingUploads.forEach(pending => {
        const placeholder = document.createElement('div');
        placeholder.className = 'thumb placeholder-thumb';
        placeholder.id = `placeholder-${pending.filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
        placeholder.innerHTML = `
          <div class="placeholder-content">
            <div class="placeholder-spinner"></div>
            <div class="placeholder-text">Converting...</div>
            <div class="placeholder-filename">${pending.filename}</div>
          </div>
        `;
        list.appendChild(placeholder);
      });
    }
    
    all.forEach((item, idx) => {
      const imageSrc = '/static_image?path=' + encodeURIComponent(item.path);
      
      // Skip if thumbnail already exists (unless doing full rebuild)
      if (!shouldFullRebuild && existingImagePaths.includes(imageSrc)) {
        return;
      }
      
      const thumb = el('div', { class: 'thumb' });
      const img = el('img', {
        src: imageSrc,
        alt: item.name,
        title: item.name
      });
      thumb.appendChild(img);
      thumb.addEventListener('click', async () => {
        if (thumb.classList.contains('disabled')) return;
        // Disable all thumbs while updating
        document.querySelectorAll('.thumb').forEach(t => t.classList.add('disabled'));
        
        try {
          await displayImage(item.path, `Applying ${item.name}...`);
        } catch (e) {
          console.error(e);
        } finally {
          // Re-enable thumbs
          document.querySelectorAll('.thumb').forEach(t => t.classList.remove('disabled'));
        }
      });
      
      // Insert in chronological order (newest first, after placeholders)
      const placeholders = list.querySelectorAll('.placeholder-thumb');
      if (placeholders.length > 0) {
        // Insert after the last placeholder
        const lastPlaceholder = placeholders[placeholders.length - 1];
        list.insertBefore(thumb, lastPlaceholder.nextSibling);
      } else {
        // No placeholders, add to the beginning (newest first)
        list.insertBefore(thumb, list.firstChild);
      }
    });
    
    console.log(`✓ Rendered ${all.length} thumbnails to #thumbList`);
  } catch (e) {
    console.error('❌ Error in refreshImages:', e);
  }
}

/**
 * Update countdown display
 */
export function updateCountdown() {
  const countdownEl = getElement('COUNTDOWN');
  const isCarouselMode = state.settings.mode === 'carousel';
  const carouselActive = state.carouselActive;
  
  if (!countdownEl) return;
  
  if (!isCarouselMode || !carouselActive || !state.lastDisplayCompletion) {
    setText('COUNTDOWN', '--');
    toggleClass('COUNTDOWN', 'disabled', true);
    return;
  }
  
  toggleClass('COUNTDOWN', 'disabled', false);
  const intervalMs = (state.settings.interval_sec || 30) * 1000;
  const completionTime = state.lastDisplayCompletion * 1000; // Convert to milliseconds
  const elapsed = Date.now() - completionTime;
  const remaining = Math.max(0, intervalMs - elapsed);
  const secondsLeft = Math.ceil(remaining / 1000);
  
  setText('COUNTDOWN', secondsLeft + 's');
}

/**
 * Update UI controls based on server status
 * @param {object} status - Status object from server
 * @param {boolean} previousBusyState - Previous busy state
 */
export function updateControlsFromStatus(status, previousBusyState) {
  const mode = (status.settings && status.settings.mode) || 'image';
  const autoplay = !!(status.settings && status.settings.autoplay);
  const intervalSec = (status.settings && status.settings.interval_sec) || 30;
  const orientation = (status.settings && status.settings.orientation) || 'portrait';
  const carouselActive = status.carousel_active || false;
  
  // Update completion timestamp from server
  if (status.last_display_completion) {
    updateState({ lastDisplayCompletion: status.last_display_completion });
  }
  
  // Update UI controls to reflect current settings
  setAttribute('MODE_IMAGE_BTN', 'aria-pressed', mode === 'image');
  setAttribute('MODE_CAROUSEL_BTN', 'aria-pressed', mode === 'carousel');
  
  const autoplayBtn = getElement('AUTOPLAY_TOGGLE');
  if (autoplayBtn) {
    autoplayBtn.textContent = 'Autoplay: ' + (autoplay ? 'On' : 'Off');
    autoplayBtn.dataset.playing = autoplay ? 'true' : 'false';
  }
  
  const intervalInput = getElement('INTERVAL_INPUT');
  if (intervalInput) intervalInput.value = intervalSec;
  
  const orientationSelect = getElement('ORIENTATION_SELECT');
  if (orientationSelect) orientationSelect.value = orientation;
  
  // Handle natural disabled states using CSS classes
  const hasImages = state.convertedImages.length > 0;
  const isCarouselMode = mode === 'carousel';
  
  // Navigation buttons disabled when no images
  toggleClass('PREV_BTN', 'disabled', !hasImages);
  toggleClass('NEXT_BTN', 'disabled', !hasImages);
  
  // Autoplay toggle only works in carousel mode
  const shouldEnableAutoplay = isCarouselMode && hasImages;
  toggleClass('AUTOPLAY_TOGGLE', 'disabled', !shouldEnableAutoplay);
  
  // Handle busy state from server - this is the key state management
  const shouldShowBusy = status.busy;
  const statusText = carouselActive && status.busy ? 'Carousel cycling...' :
                     status.busy ? 'Display busy...' : '';
  
  if (shouldShowBusy !== previousBusyState) {
    // Show current image with overlay when carousel is cycling
    if (carouselActive && status.busy && status.current_image) {
      setBusyState(shouldShowBusy, status.current_image, statusText);
    } else if (status.busy) {
      setBusyState(shouldShowBusy, null, statusText);
    } else {
      setBusyState(false);
    }
  }
  
  // Update countdown display
  updateCountdown();
}

let refreshTimer = null;

/**
 * Schedule the next refresh based on carousel state
 */
export function scheduleNextRefresh() {
  if (refreshTimer) clearTimeout(refreshTimer);
  
  // Only poll frequently if carousel is actually active on server
  const isCarouselActive = state.carouselActive;
  const interval = isCarouselActive ? 2000 : 8000; // 2 sec when carousel active, 8 sec otherwise
  
  refreshTimer = setTimeout(() => {
    refresh().then(() => scheduleNextRefresh());
  }, interval);
}

// 📋 Add placeholder thumbnails for files being uploaded/converted
export function addPendingUploadPlaceholders(uploadedFiles, originalFiles = null) {
  const thumbnailsContainer = document.getElementById('thumbList');
  
  uploadedFiles.forEach((file, index) => {
    // Skip if placeholder already exists
    if (state.pendingUploads.some(p => p.filename === file.filename)) {
      return;
    }
    
    // Add to pending state
    state.pendingUploads.push({
      filename: file.filename,
      timestamp: Date.now()
    });
    
    // Create placeholder thumbnail with optional image preview
    const placeholder = document.createElement('div');
    placeholder.className = 'thumb placeholder-thumb';
    placeholder.id = `placeholder-${file.filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
    
    // Check if we have the original File object for preview
    const originalFile = originalFiles && originalFiles[index];
    
    if (originalFile && originalFile instanceof File && originalFile.type.startsWith('image/')) {
      // Create preview with low-opacity original image
      const reader = new FileReader();
      reader.onload = function(e) {
        placeholder.innerHTML = `
          <div class="placeholder-content">
            <img src="${e.target.result}" class="placeholder-image" alt="${file.filename}" />
            <div class="placeholder-overlay">
              <div class="placeholder-spinner"></div>
              <div class="placeholder-text">Converting...</div>
            </div>
            <div class="placeholder-filename">${file.filename}</div>
          </div>
        `;
      };
      reader.readAsDataURL(originalFile);
    } else {
      // Fallback to spinner-only placeholder (for Google Photos or if no File object)
      placeholder.innerHTML = `
        <div class="placeholder-content">
          <div class="placeholder-spinner"></div>
          <div class="placeholder-text">Converting...</div>
          <div class="placeholder-filename">${file.filename}</div>
        </div>
      `;
    }
    
    // Add to thumbnails container (prepend to show newest first)
    thumbnailsContainer.insertBefore(placeholder, thumbnailsContainer.firstChild);
  });
}

// 🗑️ Remove placeholder thumbnail for converted file
export function removePendingUploadPlaceholder(filename) {
  // Remove from pending state
  state.pendingUploads = state.pendingUploads.filter(p => p.filename !== filename);
  
  // Remove DOM element
  const placeholderId = `placeholder-${filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
  const placeholder = document.getElementById(placeholderId);
  if (placeholder) {
    placeholder.remove();
  }
}
