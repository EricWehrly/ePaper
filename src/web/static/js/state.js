/**
 * Global application state management
 */

/**
 * Application state object
 */
export const state = {
  convertedImages: [],
  settings: {},
  busy: false,
  carouselActive: false,
  lastDisplayCompletion: null,
  countdownInterval: null,
  imageCounts: {
    source: 0,
    converted: 0
  }
};

/**
 * Get current state
 * @returns {object} Current state
 */
export function getState() {
  return state;
}

/**
 * Update state properties
 * @param {object} updates - Properties to update
 */
export function updateState(updates) {
  Object.assign(state, updates);
}
