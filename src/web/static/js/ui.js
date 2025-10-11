/**
 * UI refresh and update logic
 */

import { fetchJson, el } from './utils.js';
import { state, updateState } from './state.js';
import { setBusyState, displayImage } from './display.js';

/**
 * Refresh status from server and update UI
 */
export async function refresh() {
  try {
    const status = await fetchJson('/api/status');
    
    // Update current image display
    const current = status.current_image || null;
    const imgEl = document.getElementById('currentImage');
    const placeholder = document.getElementById('placeholder');
    if (current) {
      imgEl.src = '/static_image?path=' + encodeURIComponent(current);
      imgEl.style.display = '';
      placeholder.style.display = 'none';
    } else {
      imgEl.src = '';
      imgEl.style.display = 'none';
      placeholder.style.display = '';
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
    const images = await fetchJson('/api/images');
    const list = document.getElementById('thumbList');
    list.innerHTML = '';
    // Only show converted images for now
    const all = images.converted_images || [];
    updateState({ convertedImages: all });
    
    all.forEach((item, idx) => {
      const thumb = el('div', { class: 'thumb' });
      const img = el('img', {
        src: '/static_image?path=' + encodeURIComponent(item.path),
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
      list.appendChild(thumb);
    });
  } catch (e) {
    console.error(e);
  }
}

/**
 * Update countdown display
 */
export function updateCountdown() {
  const countdownEl = document.getElementById('nextImageCountdown');
  const isCarouselMode = state.settings.mode === 'carousel';
  const carouselActive = state.carouselActive;
  
  if (!isCarouselMode || !carouselActive || !state.lastDisplayCompletion) {
    countdownEl.textContent = '--';
    countdownEl.classList.add('disabled');
    return;
  }
  
  countdownEl.classList.remove('disabled');
  const intervalMs = (state.settings.interval_sec || 30) * 1000;
  const completionTime = state.lastDisplayCompletion * 1000; // Convert to milliseconds
  const elapsed = Date.now() - completionTime;
  const remaining = Math.max(0, intervalMs - elapsed);
  const secondsLeft = Math.ceil(remaining / 1000);
  
  countdownEl.textContent = secondsLeft + 's';
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
  document.getElementById('modeImageBtn').setAttribute('aria-pressed', mode === 'image');
  document.getElementById('modeCarouselBtn').setAttribute('aria-pressed', mode === 'carousel');
  const autoplayBtn = document.getElementById('autoplayToggle');
  autoplayBtn.textContent = 'Autoplay: ' + (autoplay ? 'On' : 'Off');
  autoplayBtn.dataset.playing = autoplay ? 'true' : 'false';
  document.getElementById('intervalInput').value = intervalSec;
  document.getElementById('orientationSelect').value = orientation;
  
  // Handle natural disabled states using CSS classes
  const hasImages = state.convertedImages.length > 0;
  const isCarouselMode = mode === 'carousel';
  
  // Navigation buttons disabled when no images
  ['prevBtn', 'nextBtn'].forEach(id => {
    const elRef = document.getElementById(id);
    if (hasImages) {
      elRef.classList.remove('disabled');
    } else {
      elRef.classList.add('disabled');
    }
  });
  
  // Autoplay toggle only works in carousel mode
  if (isCarouselMode && hasImages) {
    autoplayBtn.classList.remove('disabled');
  } else {
    autoplayBtn.classList.add('disabled');
  }
  
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
