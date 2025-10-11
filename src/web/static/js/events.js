/**
 * Event handlers for ePaper interface
 */

import { state, updateState } from './state.js';
import { clearDisplay, displayImage, setBusyState } from './display.js';
import { refresh, updateCountdown } from './ui.js';
import { apiPost, API_CONFIG } from './api.js';
import { getElement } from './dom.js';

/**
 * Setup all event handlers for the application
 */
export function setupEventHandlers() {
  // Clear display button
  getElement('CLEAR_BTN').addEventListener('click', () => {
    clearDisplay();
  });

  // Mode buttons
  getElement('MODE_IMAGE_BTN').addEventListener('click', async () => {
    await apiPost(API_CONFIG.ENDPOINTS.SETTINGS, { mode: 'image' });
  });

  getElement('MODE_CAROUSEL_BTN').addEventListener('click', async () => {
    await apiPost(API_CONFIG.ENDPOINTS.SETTINGS, { mode: 'carousel' });
  });

  // Navigation - Next button
  getElement('NEXT_BTN').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.classList.contains('disabled')) return;
    
    setBusyState(true, null, 'Loading next image...');
    try {
      await apiPost(API_CONFIG.ENDPOINTS.DISPLAY.NEXT, {}, false); // Don't auto-refresh
    } catch (e) {
      if (e.message !== 'busy') {
        console.error('Next image failed:', e);
      }
    } finally {
      setBusyState(false);
      setTimeout(refresh, API_CONFIG.REFRESH_DELAY);
    }
  });

  // Navigation - Previous button
  getElement('PREV_BTN').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.classList.contains('disabled')) return;
    
    setBusyState(true, null, 'Loading previous image...');
    try {
      await apiPost(API_CONFIG.ENDPOINTS.DISPLAY.PREV, {}, false); // Don't auto-refresh
    } catch (e) {
      if (e.message !== 'busy') {
        console.error('Previous image failed:', e);
      }
    } finally {
      setBusyState(false);
      setTimeout(refresh, API_CONFIG.REFRESH_DELAY);
    }
  });

  // Autoplay toggle
  getElement('AUTOPLAY_TOGGLE').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.classList.contains('disabled')) return;
    const playing = getElement('AUTOPLAY_TOGGLE').dataset.playing === 'true';
    await apiPost(API_CONFIG.ENDPOINTS.SETTINGS, { autoplay: !playing });
  });

  // Interval change
  getElement('INTERVAL_INPUT').addEventListener('change', async (e) => {
    const v = parseInt(e.target.value, 10);
    if (!isNaN(v) && v >= 5) {
      await apiPost(API_CONFIG.ENDPOINTS.SETTINGS, { interval_sec: v });
    }
  });

  // Orientation change
  getElement('ORIENTATION_SELECT').addEventListener('change', async (e) => {
    const orientation = e.target.value;
    await apiPost(API_CONFIG.ENDPOINTS.DISPLAY.ORIENTATION, { orientation }, true, 500);
  });
}

/**
 * Start countdown interval timer
 */
export function startCountdownTimer() {
  const countdownInterval = setInterval(() => {
    if (state.carouselActive) {
      updateCountdown();
    }
  }, 1000);
  
  updateState({ countdownInterval });
}
