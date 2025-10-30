/**
 * Photo Validation Module
 * 
 * Handles file validation, duplicate detection, and upload preparation
 * Used by both drag-and-drop uploads and Google Photos downloads
 */

/**
 * Validate if file is a supported image format
 * @param {File|string} file - File object or filename string
 * @returns {boolean} True if supported image format
 */
export function isValidImageFile(file) {
  const filename = typeof file === 'string' ? file : file.name;
  const extension = filename.toLowerCase().split('.').pop();
  const supportedExtensions = ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp', 'tiff', 'tif'];
  return supportedExtensions.includes(extension);
}

/**
 * Calculate file hash for duplicate detection
 * @param {File} file - File object
 * @returns {Promise<string>} File hash (SHA-1)
 */
export async function calculateFileHash(file) {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-1', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Check for duplicate files (placeholder for future implementation)
 * @param {File[]} files - Array of files to check
 * @param {Array} existingImages - Array of existing images from API
 * @returns {Promise<{duplicates: Array, unique: Array}>} Categorized files
 */
export async function checkForDuplicates(files, existingImages = []) {
  // TODO: Implement actual duplicate detection logic
  // For now, return all files as unique
  // Future implementation should compare:
  // 1. File hashes (for exact duplicates)
  // 2. Filenames (for potential duplicates)
  // 3. File sizes (for quick filtering)
  
  return {
    duplicates: [],
    unique: files.filter(isValidImageFile)
  };
}

/**
 * Prepare files for upload with validation and duplicate checking
 * @param {File[]} files - Array of files to prepare
 * @param {Array} existingImages - Existing images for duplicate check
 * @returns {Promise<{valid: File[], invalid: File[], duplicates: File[]}>}
 */
export async function prepareFilesForUpload(files, existingImages = []) {
  const valid = [];
  const invalid = [];
  
  // Basic validation
  for (const file of files) {
    if (isValidImageFile(file)) {
      valid.push(file);
    } else {
      invalid.push(file);
    }
  }
  
  // Check for duplicates
  const { duplicates, unique } = await checkForDuplicates(valid, existingImages);
  
  return {
    valid: unique,
    invalid,
    duplicates
  };
}