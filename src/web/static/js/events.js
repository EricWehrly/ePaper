/**
 * Event handlers for ePaper interface
 */

import { state, updateState } from './state.js';
import { clearDisplay, displayImage, setBusyState } from './display.js';
import { refresh, updateCountdown } from './ui.js';

/**
 * Setup all event handlers for the application
 */
export function setupEventHandlers() {
  // Clear display button
  document.getElementById('clearBtn').addEventListener('click', () => {
    clearDisplay();
  });

  // Mode buttons
  document.getElementById('modeImageBtn').addEventListener('click', async () => {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'image' })
    });
    refresh();
  });

  document.getElementById('modeCarouselBtn').addEventListener('click', async () => {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'carousel' })
    });
    refresh();
  });

  // Navigation - Next button
  document.getElementById('nextBtn').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.classList.contains('disabled')) return;
    
    setBusyState(true, null, 'Loading next image...');
    try {
      const res = await fetch('/api/display/next', { method: 'POST' });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 409) return; // Already busy
        throw new Error(errorData.error || 'next failed');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to go to next image: ' + e.message);
    } finally {
      setBusyState(false);
      setTimeout(refresh, 300);
    }
  });

  // Navigation - Previous button
  document.getElementById('prevBtn').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.classList.contains('disabled')) return;
    
    setBusyState(true, null, 'Loading previous image...');
    try {
      const res = await fetch('/api/display/prev', { method: 'POST' });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 409) return; // Already busy
        throw new Error(errorData.error || 'prev failed');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to go to previous image: ' + e.message);
    } finally {
      setBusyState(false);
      setTimeout(refresh, 300);
    }
  });

  // Autoplay toggle
  document.getElementById('autoplayToggle').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.classList.contains('disabled')) return;
    const playing = document.getElementById('autoplayToggle').dataset.playing === 'true';
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ autoplay: !playing })
    });
    setTimeout(refresh, 300);
  });

  // Interval change
  document.getElementById('intervalInput').addEventListener('change', async (e) => {
    const v = parseInt(e.target.value, 10);
    if (!isNaN(v) && v >= 5) {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_sec: v })
      });
      setTimeout(refresh, 200);
    }
  });

  // Orientation change
  document.getElementById('orientationSelect').addEventListener('change', async (e) => {
    const orientation = e.target.value;
    await fetch('/api/display/orientation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ orientation })
    });
    setTimeout(refresh, 500);
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
