/**
 * Display operations for ePaper interface
 */

import { state } from './state.js';
import { refresh } from './ui.js';
import { apiPost, API_CONFIG } from './api.js';
import { getElement, toggleClass, setVisible } from './dom.js';

/**
 * Set the busy state of the display
 * @param {boolean} busy - Whether display is busy
 * @param {string|null} incomingImagePath - Path to incoming image (optional)
 * @param {string} statusText - Status text to display (optional)
 */
export function setBusyState(busy, incomingImagePath = null, statusText = '') {
  const container = getElement('CONTAINER');
  const displayBox = getElement('DISPLAY_BOX');
  const overlay = getElement('PREVIEW_OVERLAY');
  const statusEl = getElement('PREVIEW_STATUS');
  const currentImage = getElement('CURRENT_IMAGE');
  
  if (busy) {
    // Add busy class to container - CSS will handle all disabled states
    toggleClass('CONTAINER', 'display-busy', true);
    toggleClass('DISPLAY_BOX', 'display-busy', true);
    setVisible('PREVIEW_OVERLAY', true);
    if (statusEl) statusEl.textContent = statusText;
    
    // Show incoming image if provided
    if (incomingImagePath && currentImage) {
      currentImage.src = '/static_image?path=' + encodeURIComponent(incomingImagePath);
      setVisible('CURRENT_IMAGE', true);
      setVisible('PLACEHOLDER', false);
    }
  } else {
    // Remove busy class from container - CSS will re-enable controls
    toggleClass('CONTAINER', 'display-busy', false);
    toggleClass('DISPLAY_BOX', 'display-busy', false);
    setVisible('PREVIEW_OVERLAY', false);
    if (statusEl) statusEl.textContent = '';
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
    await apiPost(API_CONFIG.ENDPOINTS.DISPLAY.IMAGE, { image_path: path }, false);
  } catch (e) {
    if (e.message !== 'busy') {
      console.error('Display image failed:', e);
    }
  } finally {
    setBusyState(false);
    setTimeout(refresh, API_CONFIG.REFRESH_DELAY);
  }
}

/**
 * Clear the ePaper display
 */
export async function clearDisplay() {
  setBusyState(true, null, 'Clearing display...');
  try {
    await apiPost(API_CONFIG.ENDPOINTS.DISPLAY.CLEAR, {}, false);
  } catch (e) {
    if (e.message !== 'busy') {
      console.error('Clear display failed:', e);
    }
  } finally {
    setBusyState(false);
    setTimeout(refresh, API_CONFIG.REFRESH_DELAY);
  }
}
