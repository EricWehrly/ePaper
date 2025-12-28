import { el } from './utils.js';
import { state, updateState } from './state.js';
import { setBusyState, displayImage } from './display.js';
import { apiGet, API_CONFIG } from './api.js';
import { getElement, setText, setAttribute, setVisible, toggleClass } from './dom.js';

export async function refresh() {
  try {
    const status = await apiGet(API_CONFIG.ENDPOINTS.STATUS);
    // HIGHEST PRIORITY: Load display preview image immediately
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

    const previousCounts = state.imageCounts;
    const newCounts = status.image_counts || { source: 0, converted: 0 };
    const countsChanged = (
      previousCounts.source !== newCounts.source || 
      previousCounts.converted !== newCounts.converted
    );

    const previousBusyState = state.busy;
    updateState({
      settings: status.settings || state.settings,
      busy: status.busy,
      carouselActive: status.carousel_active || false,
      imageCounts: newCounts
    });
    
    if (countsChanged) {
      setTimeout(refreshImages, 100);
    }
    
    updateControlsFromStatus(status, previousBusyState);
  } catch (e) {
    console.error(e);
  }
  return Promise.resolve();
}

/**
 * Load thumbnails sequentially from top to bottom for better perceived performance
 */
function loadThumbnailsSequentially(container) {
  const images = Array.from(container.querySelectorAll('img[data-src]:not(.placeholder-thumb img)'));
  
  let loadIndex = 0;
  
  function loadNext() {
    if (loadIndex >= images.length) return;
    
    const img = images[loadIndex];
    const src = img.getAttribute('data-src');
    
    if (src) {
      img.src = src;
      img.removeAttribute('data-src');
      
      img.onload = () => {
        loadIndex++;
        loadNext();
      };
      
      img.onerror = () => {
        loadIndex++;
        loadNext();
      };
    } else {
      loadIndex++;
      loadNext();
    }
  }
  
  loadNext();
}

let _refreshingImages = false;

export async function refreshImages() {
  if (_refreshingImages) return;
  
  _refreshingImages = true;
  try {
    const images = await apiGet(API_CONFIG.ENDPOINTS.IMAGES);
    const list = getElement('THUMBS_LIST');
    
    if (!list) {
      console.error('Failed to find #thumbList element');
      return;
    }
    
    const all = images.converted_images || [];
    updateState({ convertedImages: all });
    
    const convertedFilenames = all.map(img => img.name.replace(/\.bmp$/, ''));
    const completedConversions = [];
    
    state.pendingUploads.forEach(pending => {
      const originalName = pending.filename;
      const baseFilename = originalName.replace(/\.(png|jpg|jpeg|gif|webp|bmp)$/i, '');
      
      const isConverted = convertedFilenames.some(converted => {
        if (converted === baseFilename) return true;
        const cleanOriginal = baseFilename.replace(/[^\w\-_]/g, '_');
        const cleanConverted = converted.replace(/[^\w\-_]/g, '_');
        return cleanOriginal === cleanConverted;
      });
      
      if (isConverted) {
        completedConversions.push(originalName);
        removePendingUploadPlaceholder(originalName);
      }
    });
    
    const existingThumbnails = Array.from(list.children);
    const existingImagePaths = existingThumbnails
      .filter(thumb => thumb.querySelector('img'))
      .map(thumb => thumb.querySelector('img').getAttribute('src'));
    
    const shouldFullRebuild = existingThumbnails.length === 0 || completedConversions.length > 0;
    
    if (shouldFullRebuild) {
      list.innerHTML = '';
      existingImagePaths.length = 0;
      
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
    
    const srcInThisRender = new Set();
    
    all.forEach((item) => {
      const imageSrc = '/static_image?path=' + encodeURIComponent(item.path);
      
      if (srcInThisRender.has(imageSrc)) return;
      srcInThisRender.add(imageSrc);
      
      if (!shouldFullRebuild && existingImagePaths.includes(imageSrc)) return;
      
      const existingInDOM = Array.from(list.querySelectorAll('.thumb img')).find(img => {
        const existingSrc = img.getAttribute('src') || img.getAttribute('data-src');
        return existingSrc === imageSrc;
      });
      
      if (existingInDOM) return;
      
      const thumb = el('div', { class: 'thumb', draggable: 'true' });
      const img = el('img', {
        'data-src': imageSrc,
        alt: item.name,
        title: item.name,
        loading: 'lazy'
      });
      thumb.appendChild(img);
      
      thumb.addEventListener('dragstart', (e) => {
        e.dataTransfer.effectAllowed = 'copy';
        e.dataTransfer.setData('application/x-epaper-images', JSON.stringify([item.name]));
        thumb.classList.add('dragging');
      });
      
      thumb.addEventListener('dragend', () => {
        thumb.classList.remove('dragging');
      });
      
      thumb.addEventListener('click', async () => {
        if (thumb.classList.contains('disabled')) return;
        document.querySelectorAll('.thumb').forEach(t => t.classList.add('disabled'));
        
        try {
          await displayImage(item.path, `Applying ${item.name}...`);
        } catch (e) {
          console.error(e);
        } finally {
          document.querySelectorAll('.thumb').forEach(t => t.classList.remove('disabled'));
        }
      });
      
      const placeholders = list.querySelectorAll('.placeholder-thumb');
      if (placeholders.length > 0) {
        const lastPlaceholder = placeholders[placeholders.length - 1];
        list.insertBefore(thumb, lastPlaceholder.nextSibling);
      } else {
        list.insertBefore(thumb, list.firstChild);
      }
    });
    
    loadThumbnailsSequentially(list);
  } catch (e) {
    console.error('Error in refreshImages:', e);
  } finally {
    _refreshingImages = false;
  }
}

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

export function updateControlsFromStatus(status, previousBusyState) {
  const mode = (status.settings && status.settings.mode) || 'image';
  const autoplay = !!(status.settings && status.settings.autoplay);
  const intervalSec = (status.settings && status.settings.interval_sec) || 30;
  const orientation = (status.settings && status.settings.orientation) || 'portrait';
  const carouselActive = status.carousel_active || false;
  
  if (status.last_display_completion) {
    updateState({ lastDisplayCompletion: status.last_display_completion });
  }
  
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
  
  const hasImages = state.convertedImages.length > 0;
  const isCarouselMode = mode === 'carousel';
  
  toggleClass('PREV_BTN', 'disabled', !hasImages);
  toggleClass('NEXT_BTN', 'disabled', !hasImages);
  
  const shouldEnableAutoplay = isCarouselMode && hasImages;
  toggleClass('AUTOPLAY_TOGGLE', 'disabled', !shouldEnableAutoplay);
  
  const shouldShowBusy = status.busy;
  const statusText = carouselActive && status.busy ? 'Carousel cycling...' :
                     status.busy ? 'Display busy...' : '';
  
  if (shouldShowBusy !== previousBusyState) {
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

export function scheduleNextRefresh() {
  if (refreshTimer) clearTimeout(refreshTimer);
  
  const isCarouselActive = state.carouselActive;
  const interval = isCarouselActive ? 2000 : 8000;
  refreshTimer = setTimeout(() => {
    refresh().then(() => scheduleNextRefresh());
  }, interval);
}

export function addPendingUploadPlaceholders(uploadedFiles, originalFiles = null) {
  const thumbnailsContainer = document.getElementById('thumbList');
  
  uploadedFiles.forEach((file, index) => {
    if (state.pendingUploads.some(p => p.filename === file.filename)) return;
    
    state.pendingUploads.push({
      filename: file.filename,
      timestamp: Date.now()
    });
    
    const placeholder = document.createElement('div');
    placeholder.className = 'thumb placeholder-thumb';
    placeholder.id = `placeholder-${file.filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
    
    const originalFile = originalFiles && originalFiles[index];
    
    if (originalFile && originalFile instanceof File && originalFile.type.startsWith('image/')) {
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
      placeholder.innerHTML = `
        <div class="placeholder-content">
          <div class="placeholder-spinner"></div>
          <div class="placeholder-text">Converting...</div>
          <div class="placeholder-filename">${file.filename}</div>
        </div>
      `;
    }
    
    thumbnailsContainer.insertBefore(placeholder, thumbnailsContainer.firstChild);
  });
}

export function removePendingUploadPlaceholder(filename) {
  state.pendingUploads = state.pendingUploads.filter(p => p.filename !== filename);
  
}
