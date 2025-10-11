/**
 * Utility functions for the ePaper web interface
 */

import { apiGet } from './api.js';

/**
 * Fetch and parse JSON from a URL (legacy wrapper)
 * @deprecated Use apiGet from api.js instead
 * @param {string} path - URL path to fetch
 * @returns {Promise<object>} Parsed JSON response
 */
export async function fetchJson(path) {
  return apiGet(path, false); // Don't auto-refresh for legacy calls
}

/**
 * Create a DOM element with attributes and children
 * @param {string} tag - HTML tag name
 * @param {object} attrs - Element attributes
 * @param {...(string|Element)} children - Child elements or text
 * @returns {Element} Created element
 */
export function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') e.className = v;
    else e.setAttribute(k, v);
  });
  children.forEach(c => {
    if (typeof c === 'string') e.appendChild(document.createTextNode(c));
    else e.appendChild(c);
  });
  return e;
}

/**
 * Debounce function calls to prevent excessive API requests
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, delay) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * Generate a safe DOM ID from a filename
 * @param {string} filename - Original filename
 * @returns {string} Safe ID string
 */
export function createSafeId(filename) {
  return filename.replace(/[^a-zA-Z0-9]/g, '_');
}

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted size string
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
