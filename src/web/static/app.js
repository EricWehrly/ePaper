/**
 * ePaper Display Web Interface - Main Entry Point
 * 
 * This is the main application file that imports all modules
 * and initializes the ePaper web interface.
 */

import { refreshImages, refresh, scheduleNextRefresh } from './js/ui.js';
import { setupEventHandlers, startCountdownTimer } from './js/events.js';

/**
 * Initialize the application when DOM is loaded
 */
window.addEventListener('load', () => {
  // Load images list once at startup (images rarely change)
  refreshImages().then(() => {
    // Then start regular status polling
    refresh().then(() => scheduleNextRefresh());
  });
  
  // Start countdown update timer (every second when carousel is active)
  startCountdownTimer();
  
  // Setup all event handlers
  setupEventHandlers();
});