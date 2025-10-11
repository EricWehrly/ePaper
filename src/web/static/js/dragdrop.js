/**
 * Drag-and-drop file upload functionality for ePaper interface
 */

import { refreshImages, addPendingUploadPlaceholders } from './ui.js';
import { apiUpload, API_CONFIG, isSupportedImageFile } from './api.js';
import { getElement, toggleClass } from './dom.js';

/**
 * Check if drag event contains files (actual type check happens on drop)
 * @param {DragEvent} e - Drag event
 * @returns {boolean} True if drag contains files
 */
function hasFiles(e) {
  if (!e.dataTransfer) return false;
  return Array.from(e.dataTransfer.types).includes('Files');
}

/**
 * Show the drop zone overlay
 */
function showDropZone() {
  toggleClass('DISPLAY_BOX', 'drag-over', true);
}

/**
 * Hide the drop zone overlay
 */
function hideDropZone() {
  toggleClass('DISPLAY_BOX', 'drag-over', false);
}

/**
 * Handle dragenter event
 */
function handleDragEnter(e) {
  e.preventDefault();
  e.stopPropagation();
  
  // Show drop zone if dragging files
  if (hasFiles(e)) {
    showDropZone();
  }
}

/**
 * Handle dragover event
 */
function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  
  // Set dropEffect for visual feedback
  if (hasFiles(e)) {
    e.dataTransfer.dropEffect = 'copy';
  } else {
    e.dataTransfer.dropEffect = 'none';
  }
}

/**
 * Handle dragleave event
 */
function handleDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  
  // Only hide if leaving the displayBox entirely
  // Check if the related target is outside displayBox
  const displayBox = getElement('DISPLAY_BOX');
  if (!displayBox.contains(e.relatedTarget)) {
    hideDropZone();
  }
}

/**
 * Handle drop event
 */
async function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  
  hideDropZone();
  
  const files = Array.from(e.dataTransfer.files);
  const supportedFiles = files.filter(isSupportedImageFile);
  
  if (supportedFiles.length === 0) {
    // TODO: Add toast notification system for better user feedback
    console.log(`⚠️ No supported image files detected. Supported formats: ${API_CONFIG.SUPPORTED_EXTENSIONS.join(', ')}`);
    return;
  }
  
  // TODO: Add loading spinner/progress indicator
  console.log(`📤 Uploading ${supportedFiles.length} image file(s)...`);
  
  try {
    await uploadFiles(supportedFiles);
    console.log(`✅ Successfully uploaded ${supportedFiles.length} file(s) - conversion started`);
  } catch (error) {
    // Error handling is now centralized in apiUpload
    console.error('❌ Upload failed:', error);
  }
}

/**
 * Upload files to the server
 * @param {File[]} files - Array of files to upload
 */
async function uploadFiles(files) {
  const formData = new FormData();
  
  files.forEach(file => {
    formData.append('files', file);
  });
  
  const result = await apiUpload(API_CONFIG.ENDPOINTS.UPLOAD, formData);
  console.log('📁 Files saved to pic-raw/, queued for conversion:', result.uploaded_files.map(f => f.filename));
  
  // Add placeholder thumbnails for uploaded files
  addPendingUploadPlaceholders(result.uploaded_files);
  
  // Refresh handled automatically by apiUpload
  console.log(`${result.count} files queued for conversion`);
}

/**
 * Setup drag-and-drop functionality
 */
export function setupDragDrop() {
  const displayBox = getElement('DISPLAY_BOX');
  
  if (!displayBox) {
    console.error('displayBox element not found');
    return;
  }
  
  // Prevent default drag behavior on document to enable custom drop zones
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => e.preventDefault());
  
  // Add event listeners for drag-and-drop on display box
  displayBox.addEventListener('dragenter', handleDragEnter);
  displayBox.addEventListener('dragover', handleDragOver);
  displayBox.addEventListener('dragleave', handleDragLeave);
  displayBox.addEventListener('drop', handleDrop);
  
  // Drag-and-drop ready
}