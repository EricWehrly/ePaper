/**
 * Drag-and-drop file upload functionality for ePaper interface
 */

import { refreshImages, addPendingUploadPlaceholders, removePendingUploadPlaceholder } from './ui.js';

/**
 * Supported image file extensions for drag-and-drop
 */
const SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'];

/**
 * Check if a file has a supported image extension
 * @param {File} file - File object to check
 * @returns {boolean} True if file type is supported
 */
function isSupportedImageFile(file) {
  const fileName = file.name.toLowerCase();
  return SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext));
}

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
  const displayBox = document.getElementById('displayBox');
  displayBox.classList.add('drag-over');
}

/**
 * Hide the drop zone overlay
 */
function hideDropZone() {
  const displayBox = document.getElementById('displayBox');
  displayBox.classList.remove('drag-over');
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
  const displayBox = document.getElementById('displayBox');
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
    console.log('⚠️ No supported image files detected. Supported formats: PNG, JPG, BMP, GIF, WebP, TIFF');
    return;
  }
  
  // TODO: Add loading spinner/progress indicator
  console.log(`📤 Uploading ${supportedFiles.length} image file(s)...`);
  
  try {
    await uploadFiles(supportedFiles);
    // TODO: Replace with toast notification
    console.log(`✅ Successfully uploaded ${supportedFiles.length} file(s) - conversion started`);
  } catch (error) {
    console.error('❌ Upload failed:', error);
    // TODO: Replace with toast notification  
    alert('Upload failed: ' + error.message);
  }
}

/**
 * Upload files to the server
 * @param {File[]} files - Array of files to upload
 */
async function uploadFiles(files) {
  const formData = new FormData();
  
  files.forEach((file, index) => {
    formData.append('files', file);
  });
  
  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }
  
  const result = await response.json();
  console.log('📁 Files saved to pic-raw/, queued for conversion:', result.uploaded_files.map(f => f.filename));
  
  // Add placeholder thumbnails for uploaded files
  addPendingUploadPlaceholders(result.uploaded_files);
  
  // Refresh the images list after upload to show any completed conversions
  setTimeout(refreshImages, 500);
  
  // TODO: In Phase 2, we'll add queue monitoring here
  // For now, just show success message
  console.log(`${result.count} files queued for conversion`);
}

/**
 * Setup drag-and-drop functionality
 */
export function setupDragDrop() {
  const displayBox = document.getElementById('displayBox');
  
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