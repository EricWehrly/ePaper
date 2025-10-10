/**
 * Display operations for ePaper interface
 */

import { state } from './state.js';
import { refresh } from './ui.js';

/**
 * Set the busy state of the display
 * @param {boolean} busy - Whether display is busy
 * @param {string|null} incomingImagePath - Path to incoming image (optional)
 * @param {string} statusText - Status text to display (optional)
 */
export function setBusyState(busy, incomingImagePath = null, statusText = '') {
  const container = document.querySelector('.container');
  const displayBox = document.getElementById('displayBox');
  const overlay = document.getElementById('previewOverlay');
  const statusEl = document.getElementById('previewStatus');
  const currentImage = document.getElementById('currentImage');
  
  if (busy) {
    // Add busy class to container - CSS will handle all disabled states
    container.classList.add('display-busy');
    displayBox.classList.add('display-busy');
    overlay.style.display = 'block';
    statusEl.textContent = statusText;
    
    // Show incoming image if provided
    if (incomingImagePath) {
      currentImage.src = '/static_image?path=' + encodeURIComponent(incomingImagePath);
      currentImage.style.display = '';
      document.getElementById('placeholder').style.display = 'none';
    }
  } else {
    // Remove busy class from container - CSS will re-enable controls
    container.classList.remove('display-busy');
    displayBox.classList.remove('display-busy');
    overlay.style.display = 'none';
    statusEl.textContent = '';
  }
}

/**
 * Display an image on the ePaper
 * @param {string} path - Path to image file
 * @param {string} statusText - Status text to display
 */
export async function displayImage(path, statusText = 'Applying image...') {
  setBusyState(true, path, statusText);
  try {
    const res = await fetch('/api/display/image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_path: path })
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      if (res.status === 409) {
        // Display is busy, don't change UI state
        return;
      }
      throw new Error(errorData.error || 'display failed');
    }
  } catch (e) {
    console.error(e);
    alert('Failed to display image: ' + e.message);
  } finally {
    setBusyState(false);
    setTimeout(refresh, 300);
  }
}

/**
 * Clear the ePaper display
 */
export async function clearDisplay() {
  setBusyState(true, null, 'Clearing display...');
  try {
    const res = await fetch('/api/display/clear', { method: 'POST' });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      if (res.status === 409) return; // Already busy
      throw new Error(errorData.error || 'clear failed');
    }
  } catch (e) {
    console.error(e);
    alert('Failed to clear display: ' + e.message);
  } finally {
    setBusyState(false);
    setTimeout(refresh, 300);
  }
}
