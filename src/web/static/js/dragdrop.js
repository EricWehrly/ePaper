import { API_CONFIG, isSupportedImageFile } from './api.js';
import { getElement, toggleClass } from './dom.js';

function hasFiles(e) {
  if (!e.dataTransfer) return false;
  return Array.from(e.dataTransfer.types).includes('Files');
}

function showDropZone() {
  toggleClass('DISPLAY_BOX', 'drag-over', true);
}

function hideDropZone() {
  toggleClass('DISPLAY_BOX', 'drag-over', false);
}

function handleDragEnter(e) {
  e.preventDefault();
  e.stopPropagation();
  
  // Show drop zone if dragging files
  if (hasFiles(e)) {
    showDropZone();
  }
}

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

async function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  
  hideDropZone();
  
  const files = Array.from(e.dataTransfer.files);
  const supportedFiles = files.filter(isSupportedImageFile);
  
  if (supportedFiles.length === 0) {
    console.log(`⚠️ No supported image files detected. Supported formats: ${API_CONFIG.SUPPORTED_EXTENSIONS.join(', ')}`);
    return;
  }
  
  console.log(`📤 Uploading ${supportedFiles.length} image file(s)...`);
  
  try {
    await uploadFiles(supportedFiles);
    console.log(`✅ Successfully uploaded ${supportedFiles.length} file(s) - conversion started`);
  } catch (error) {
    // Error handling is now centralized in apiUpload
    console.error('❌ Upload failed:', error);
  }
}


async function uploadFiles(files) {
  // Use shared upload module for consistency with Google Photos
  const { uploadPhotos, handleUploadError } = await import('./photo_upload.js');
  
  try {
    const result = await uploadPhotos(files);
    console.log(`${result.uploaded_files?.length || 0} files queued for conversion`);
  } catch (error) {
    handleUploadError(error, 'drag-and-drop upload');
    throw error; // Re-throw for existing error handling
  }
}


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