/**
 * API utilities and standardized request handling
 */

import { refresh } from './ui.js';

/**
 * Configuration constants
 */
export const API_CONFIG = {
  // Timeout values
  REFRESH_DELAY: 300,
  UPLOAD_REFRESH_DELAY: 500,
  
  // Supported file extensions
  SUPPORTED_EXTENSIONS: ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'],
  
  // API endpoints
  ENDPOINTS: {
    STATUS: '/api/status',
    IMAGES: '/api/images', 
    UPLOAD: '/api/upload',
    SETTINGS: '/api/settings',
    DISPLAY: {
      IMAGE: '/api/display/image',
      CLEAR: '/api/display/clear',
      NEXT: '/api/display/next',
      PREV: '/api/display/prev',
      ORIENTATION: '/api/display/orientation'
    }
  }
};

/**
 * Standardized API request wrapper with consistent error handling
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options (method, headers, body, etc.)
 * @param {boolean} autoRefresh - Whether to refresh UI after successful request
 * @param {number} refreshDelay - Delay before refreshing UI
 * @returns {Promise<object>} API response data
 */
export async function apiRequest(url, options = {}, autoRefresh = true, refreshDelay = API_CONFIG.REFRESH_DELAY) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      // Handle specific HTTP status codes
      if (response.status === 409) {
        // Display is busy - this is expected, don't show error
        return { busy: true };
      }
      
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Auto-refresh UI after successful API calls
    if (autoRefresh) {
      setTimeout(refresh, refreshDelay);
    }
    
    return data;
    
  } catch (error) {
    console.error(`API request failed (${url}):`, error);
    
    // TODO: Replace with toast notification system
    // For now, use alert for user-facing errors
    if (error.message !== 'busy') {
      alert(`Request failed: ${error.message}`);
    }
    
    throw error;
  }
}

/**
 * Convenience method for GET requests
 */
export async function apiGet(url, autoRefresh = false) {
  return apiRequest(url, { method: 'GET' }, autoRefresh);
}

/**
 * Convenience method for POST requests with JSON body
 */
export async function apiPost(url, data = {}, autoRefresh = true) {
  return apiRequest(url, {
    method: 'POST',
    body: JSON.stringify(data)
  }, autoRefresh);
}

/**
 * Convenience method for file uploads (multipart/form-data)
 */
export async function apiUpload(url, formData, autoRefresh = true) {
  return apiRequest(url, {
    method: 'POST',
    body: formData,
    headers: {} // Don't set Content-Type for FormData
  }, autoRefresh, API_CONFIG.UPLOAD_REFRESH_DELAY);
}

/**
 * Check if a file has a supported image extension
 * @param {File|string} file - File object or filename string
 * @returns {boolean} True if file type is supported
 */
export function isSupportedImageFile(file) {
  const fileName = (typeof file === 'string' ? file : file.name).toLowerCase();
  return API_CONFIG.SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext));
}