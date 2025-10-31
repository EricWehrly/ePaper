/**
 * ePaper Display Web Interface - Main Entry Point
 * 
 * This is the main application file that imports all modules
 * and initializes the ePaper web interface.
 */

import { refreshImages, refresh, scheduleNextRefresh } from './js/ui.js';
import { setupEventHandlers, startCountdownTimer } from './js/events.js';
import { setupDragDrop } from './js/dragdrop.js';
import { updatePageTitle, updateAppHeading } from './js/app_config.js';
import { initializePlaylists } from './js/playlists.js';

/**
 * Set favicon with emoji using JavaScript for better readability
 * @param {string} emoji - Emoji to use as favicon
 */
function setFavicon(emoji = '📷') {
  const favicon = document.createElement('link');
  favicon.rel = 'icon';
  favicon.href = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <text x="50%" y="50%" text-anchor="middle" dominant-baseline="central" font-size="80">${emoji}</text>
  </svg>`;
  document.head.appendChild(favicon);
}

/**
 * Initialize the application when DOM is loaded
 */
window.addEventListener('load', () => {
  // Set up favicon and dynamic page elements
  setFavicon();
  updatePageTitle();
  updateAppHeading();
  // Load images list once at startup (images rarely change)
  refreshImages().then(() => {
    // Then start regular status polling
    refresh().then(() => scheduleNextRefresh());
  });
  
  // Start countdown update timer (every second when carousel is active)
  startCountdownTimer();
  
  // Setup all event handlers
  setupEventHandlers();
  
  // Setup drag-and-drop functionality
  setupDragDrop();
  
  // Initialize playlist functionality
  initializePlaylists();
});