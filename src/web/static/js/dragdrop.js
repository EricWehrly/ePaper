/**
 * Drag-and-drop file upload functionality for ePaper interface
 */

import { refreshImages } from './ui.js';

/**
 * Supported image file extensions for drag-and-drop
 */
const SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg'];

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
 * Check if drag event contains supported image files
 * @param {DragEvent} e - Drag event
 * @returns {boolean} True if any files are supported images
 */
function hasSupportedFiles(e) {
  if (!e.dataTransfer) return false;
  
  // Check types array for image types
  const types = Array.from(e.dataTransfer.types);
  console.log('Drag types:', types);
  
  // If we have Files type, assume it might contain images
  // We'll do the real check on drop
  return types.includes('Files');
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
  console.log('dragenter event triggered');
  e.preventDefault();
  e.stopPropagation();
  
  // Only show drop zone if dragging supported files
  if (hasSupportedFiles(e)) {
    console.log('Supported files detected, showing drop zone');
    showDropZone();
  } else {
    console.log('No supported files detected in drag');
  }
}

/**
 * Handle dragover event
 */
function handleDragOver(e) {
  console.log('dragover event triggered');
  e.preventDefault();
  e.stopPropagation();
  
  // Set dropEffect for visual feedback
  if (hasSupportedFiles(e)) {
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
    console.log('No supported image files dropped');
    return;
  }
  
  console.log(`Uploading ${supportedFiles.length} image file(s)...`);
  
  try {
    await uploadFiles(supportedFiles);
  } catch (error) {
    console.error('Upload failed:', error);
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
  console.log('Upload successful:', result);
  
  // Refresh the images list after upload
  setTimeout(refreshImages, 300);
  
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
  
  console.log('Setting up drag-and-drop on displayBox:', displayBox);
  
  // Add temporary test indicator
  displayBox.style.border = '2px solid red';
  setTimeout(() => {
    displayBox.style.border = '';
  }, 2000);
  
  // Prevent default drag behavior on document to enable custom drop zones
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => e.preventDefault());
  
  // Add event listeners for drag-and-drop on display box
  displayBox.addEventListener('dragenter', handleDragEnter);
  displayBox.addEventListener('dragover', handleDragOver);
  displayBox.addEventListener('dragleave', handleDragLeave);
  displayBox.addEventListener('drop', handleDrop);
  
  console.log('Drag-and-drop functionality initialized successfully');
}