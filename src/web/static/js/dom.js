/**
 * DOM utilities and element caching
 */

/**
 * Cached DOM elements to avoid repeated queries
 */
const domCache = new Map();

/**
 * Element selectors - centralized for easy maintenance
 */
const SELECTORS = {
  // Main containers
  CONTAINER: '.container',
  DISPLAY_BOX: '#displayBox',
  THUMBS_LIST: '#thumbList',
  
  // Display elements
  CURRENT_IMAGE: '#currentImage',
  PLACEHOLDER: '#placeholder',
  PREVIEW_OVERLAY: '#previewOverlay',
  PREVIEW_STATUS: '#previewStatus',
  
  // Control buttons
  CLEAR_BTN: '#clearBtn',
  MODE_IMAGE_BTN: '#modeImageBtn',
  MODE_CAROUSEL_BTN: '#modeCarouselBtn',
  NEXT_BTN: '#nextBtn',
  PREV_BTN: '#prevBtn',
  AUTOPLAY_TOGGLE: '#autoplayToggle',
  
  // Form inputs
  INTERVAL_INPUT: '#intervalInput',
  ORIENTATION_SELECT: '#orientationSelect',
  
  // Status displays
  COUNTDOWN: '#nextImageCountdown'
};

/**
 * Get cached DOM element or query and cache it
 * @param {string} selector - CSS selector or SELECTOR key
 * @returns {Element|null} DOM element
 */
export function getElement(selector) {
  // Use predefined selector if it's a key
  const actualSelector = SELECTORS[selector] || selector;
  
  if (!domCache.has(actualSelector)) {
    const element = document.querySelector(actualSelector);
    domCache.set(actualSelector, element);
  }
  
  return domCache.get(actualSelector);
}

/**
 * Get multiple cached elements
 * @param {string} selector - CSS selector
 * @returns {NodeList} List of DOM elements
 */
export function getElements(selector) {
  const cacheKey = `${selector}:all`;
  
  if (!domCache.has(cacheKey)) {
    const elements = document.querySelectorAll(selector);
    domCache.set(cacheKey, elements);
  }
  
  return domCache.get(cacheKey);
}

/**
 * Clear DOM cache (call when DOM structure changes)
 */
export function clearDomCache() {
  domCache.clear();
}

/**
 * Add/remove CSS class utility with element caching
 * @param {string} selector - Element selector
 * @param {string} className - CSS class to toggle
 * @param {boolean} add - True to add, false to remove
 */
export function toggleClass(selector, className, add) {
  const element = getElement(selector);
  if (element) {
    if (add) {
      element.classList.add(className);
    } else {
      element.classList.remove(className);
    }
  }
}

/**
 * Set element text content with caching
 * @param {string} selector - Element selector
 * @param {string} text - Text content to set
 */
export function setText(selector, text) {
  const element = getElement(selector);
  if (element) {
    element.textContent = text;
  }
}

/**
 * Set element attribute with caching
 * @param {string} selector - Element selector
 * @param {string} attribute - Attribute name
 * @param {string} value - Attribute value
 */
export function setAttribute(selector, attribute, value) {
  const element = getElement(selector);
  if (element) {
    element.setAttribute(attribute, value);
  }
}

/**
 * Get element's current attribute value
 * @param {string} selector - Element selector  
 * @param {string} attribute - Attribute name
 * @returns {string|null} Attribute value
 */
export function getAttribute(selector, attribute) {
  const element = getElement(selector);
  return element ? element.getAttribute(attribute) : null;
}

/**
 * Show/hide element utility
 * @param {string} selector - Element selector
 * @param {boolean} show - True to show, false to hide
 */
export function setVisible(selector, show) {
  const element = getElement(selector);
  if (element) {
    element.style.display = show ? '' : 'none';
  }
}

// Export selectors for direct access if needed
export { SELECTORS };