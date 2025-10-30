/**
 * Photo Upload Module
 * 
 * Shared upload logic for both drag-and-drop and Google Photos
 * Handles validation, duplicate detection, and upload processing
 */

import { apiUpload, API_CONFIG } from './api.js';
import { prepareFilesForUpload } from './photo_validation.js';
import { addPendingUploadPlaceholders } from './ui.js';

/**
 * Upload files with validation and duplicate checking
 * @param {File[]} files - Array of files to upload
 * @param {Array} existingImages - Existing images for duplicate check
 * @returns {Promise<Object>} Upload result
 */
export async function uploadPhotos(files, existingImages = []) {
  console.log(`📤 Processing ${files.length} file(s) for upload...`);
  
  // Validate and check for duplicates
  const { valid, invalid, duplicates } = await prepareFilesForUpload(files, existingImages);
  
  if (invalid.length > 0) {
    console.warn(`⚠️ Skipping ${invalid.length} invalid file(s):`, invalid.map(f => f.name));
  }
  
  if (duplicates.length > 0) {
    console.warn(`🔄 Found ${duplicates.length} potential duplicate(s):`, duplicates.map(f => f.name));
    // TODO: Show user confirmation dialog for duplicates
  }
  
  if (valid.length === 0) {
    throw new Error('No valid files to upload');
  }
  
  // Create FormData for upload
  const formData = new FormData();
  valid.forEach(file => {
    formData.append('files', file);
  });
  
  // Upload to server
  const result = await apiUpload(API_CONFIG.ENDPOINTS.UPLOAD, formData);
  console.log('📁 Files uploaded and queued for conversion:', result.uploaded_files.map(f => f.filename));
  
  // Add placeholder thumbnails
  addPendingUploadPlaceholders(result.uploaded_files, valid);
  
  return {
    ...result,
    skipped: {
      invalid: invalid.map(f => f.name),
      duplicates: duplicates.map(f => f.name)
    }
  };
}

/**
 * Handle file upload errors with user-friendly messages
 * @param {Error} error - Upload error
 * @param {string} context - Context where error occurred
 */
export function handleUploadError(error, context = 'upload') {
  console.error(`❌ ${context} failed:`, error);
  
  // TODO: Show user-friendly error toast
  // For now, log the error details
  if (error.message.includes('413')) {
    console.error('File too large - consider resizing images before upload');
  } else if (error.message.includes('network')) {
    console.error('Network error - check connection and try again');
  } else {
    console.error('Upload failed - please try again');
  }
}