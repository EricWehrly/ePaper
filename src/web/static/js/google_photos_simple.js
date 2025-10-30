/**
 * Simple Google Photos Picker Integration
 * Streamlined interface with just picker button and status updates
 */

class SimpleGooglePhotos {
    constructor() {
        this.authenticated = false;
        this.currentSession = null;
        this.pollingInterval = null;
        
        this.init();
    }

    async init() {
        console.log('SimpleGooglePhotos initializing...');
        this.setupEventListeners();
        await this.checkNgrokRedirect();
        await this.checkAuthStatus();
    }

    setupEventListeners() {
        // Toggle section
        const toggleBtn = document.getElementById('toggleGooglePhotos');
        toggleBtn?.addEventListener('click', () => this.toggleSection());

        // Auth buttons
        const loginBtn = document.getElementById('loginBtn');
        loginBtn?.addEventListener('click', () => this.handleAuth());

        const logoutBtn = document.getElementById('logoutBtn');
        logoutBtn?.addEventListener('click', () => this.handleDisconnect());

        // Picker button
        const openPickerBtn = document.getElementById('openPickerBtn');
        openPickerBtn?.addEventListener('click', () => this.openPhotoPicker());
    }

    async checkNgrokRedirect() {
        if (!window.location.hostname.includes('raspberrypi.local')) return;

        try {
            const response = await fetch('/api/google-photos/ngrok-info');
            const data = await response.json();
            
            if (data.ngrok_url && data.should_redirect && !data.authenticated) {
                this.showNgrokBanner(data.ngrok_url);
            }
        } catch (error) {
            console.log('Ngrok check failed (expected if not available):', error.message);
        }
    }

    showNgrokBanner(ngrokUrl) {
        const banner = document.createElement('div');
        banner.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
            background: #2563eb; color: white; padding: 12px; text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        `;
        banner.innerHTML = `
            <strong>📸 Google Photos Authentication Required:</strong>
            <a href="${ngrokUrl}" style="color: #fbbf24; text-decoration: underline; margin: 0 8px;">
                Use ${ngrokUrl} for Google Photos
            </a>
            <button onclick="this.parentElement.remove()" style="background: none; border: 1px solid white; color: white; padding: 4px 8px; margin-left: 8px; border-radius: 4px; cursor: pointer;">×</button>
        `;
        document.body.insertBefore(banner, document.body.firstChild);
        document.body.style.paddingTop = '60px';
    }

    toggleSection() {
        const section = document.getElementById('googlePhotosSection');
        const container = section.closest('.google-photos-container');
        const isVisible = section.style.display !== 'none';
        
        section.style.display = isVisible ? 'none' : 'block';
        
        // Update expanded class on container for styling
        if (container) {
            if (isVisible) {
                container.classList.remove('google-photos-expanded');
            } else {
                container.classList.add('google-photos-expanded');
            }
        }
        
        if (!isVisible && !this.authenticated) {
            this.checkAuthStatus();
        }
    }

    async checkAuthStatus() {
        this.updateStatus('Checking authentication...');
        
        try {
            const response = await fetch('/api/google-photos/status');
            const data = await response.json();
            
            this.authenticated = data.authenticated;
            this.updateAuthUI(data);
            
        } catch (error) {
            console.error('Failed to check auth status:', error);
            this.updateStatus('Failed to check authentication status', 'error');
        }
    }

    updateAuthUI(authData) {
        const authStatusText = document.getElementById('authStatusText');
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const pickerSection = document.getElementById('pickerSection');
        const pickerStatus = document.getElementById('pickerStatus');
        const section = document.getElementById('googlePhotosSection');
        const container = section?.closest('.google-photos-container');

        if (authData.authenticated) {
            authStatusText.textContent = `Signed in as ${authData.user?.email || 'Google user'}`;
            loginBtn.style.display = 'none';
            logoutBtn.style.display = 'inline-block';
            pickerSection.style.display = 'block';
            pickerStatus.style.display = 'block';
            this.updateStatus('Ready to select photos');
            
            // Auto-expand section when user is logged in
            if (section && container) {
                section.style.display = 'block';
                container.classList.add('google-photos-expanded');
            }
        } else {
            authStatusText.textContent = 'Not signed in to Google Photos';
            loginBtn.style.display = 'inline-block';
            logoutBtn.style.display = 'none';
            pickerSection.style.display = 'none';
            pickerStatus.style.display = 'none';
            this.updateStatus('Sign in required');
            
            // Don't force-close section when not authenticated - let user toggle manually
            // Only auto-expand if authenticated, but never auto-collapse
        }
    }

    updateStatus(message, type = 'info') {
        const statusElement = document.getElementById('pickerStatusText');
        const statusContainer = document.getElementById('pickerStatus');
        
        if (statusElement) {
            statusElement.textContent = message;
        }
        
        if (statusContainer) {
            // Reset classes
            statusContainer.className = 'picker-status';
            
            // Add type-specific class
            if (type !== 'info') {
                statusContainer.classList.add(type);
            }
        }
        
        console.log(`GooglePhotos Status [${type}]:`, message);
    }

    async handleAuth() {
        this.updateStatus('Redirecting to Google authentication...');
        window.location.href = '/api/google-photos/auth';
    }

    async handleDisconnect() {
        this.updateStatus('Signing out...');
        
        try {
            const response = await fetch('/api/google-photos/disconnect', { method: 'POST' });
            
            if (response.ok) {
                this.authenticated = false;
                this.updateStatus('Signed out successfully');
                await this.checkAuthStatus();
            } else {
                this.updateStatus('Failed to sign out', 'error');
            }
        } catch (error) {
            console.error('Disconnect failed:', error);
            this.updateStatus('Sign out failed', 'error');
        }
    }

    async openPhotoPicker() {
        if (!this.authenticated) {
            this.updateStatus('Please sign in first', 'error');
            return;
        }

        this.updateStatus('Creating picker session...', 'waiting');
        
        try {
            // Create picker session
            const sessionResponse = await fetch('/api/google-photos/create-session', { 
                method: 'POST' 
            });
            
            if (!sessionResponse.ok) {
                throw new Error(`Session creation failed: ${sessionResponse.status}`);
            }
            
            const sessionData = await sessionResponse.json();
            this.currentSession = sessionData.session;
            
            this.updateStatus('Opening Google Photos picker...', 'waiting');
            
            // Open picker in popup with autoclose as path parameter
            const pickerUrl = this.currentSession.pickerUri.endsWith('/') 
                ? this.currentSession.pickerUri + 'autoclose'
                : this.currentSession.pickerUri + '/autoclose';
            
            const pickerWindow = window.open(
                pickerUrl,
                'googlePhotosPicker',
                'width=800,height=600,scrollbars=yes,resizable=yes'
            );

            if (!pickerWindow) {
                throw new Error('Failed to open picker window. Please allow popups for this site.');
            }

            // Start polling for selection
            this.startPolling(pickerWindow);
            
        } catch (error) {
            console.error('Failed to open picker:', error);
            this.updateStatus(`Picker error: ${error.message}`, 'error');
        }
    }

    startPolling(pickerWindow) {
        this.updateStatus('Waiting for photo selection...', 'waiting');
        
        let selectionComplete = false;
        let startTime = Date.now();
        
        // Monitor window closure but be patient about cancellation detection
        const checkClosed = setInterval(() => {
            if (pickerWindow.closed && !selectionComplete) {
                clearInterval(checkClosed);
                
                const elapsedTime = Date.now() - startTime;
                console.log(`Picker window closed after ${elapsedTime}ms, selectionComplete: ${selectionComplete}`);
                
                // Be much more patient - give plenty of time to detect selection
                // Don't treat as cancelled unless window was open for meaningful time AND no selection detected
                const minTimeForSelection = 10000; // 10 seconds minimum
                const waitTimeAfterClose = 10000; // Wait 10 seconds after close to check for selection
                
                if (elapsedTime > minTimeForSelection) {
                    // Window was open long enough, give time to detect selection
                    setTimeout(() => {
                        if (!selectionComplete && this.pollingInterval) {
                            clearInterval(this.pollingInterval);
                            this.pollingInterval = null;
                            console.log('Treating window closure as cancellation after reasonable wait');
                            this.updateStatus('Photo selection cancelled');
                        }
                    }, waitTimeAfterClose);
                } else {
                    // Window closed very quickly - likely autoclose, keep polling longer
                    setTimeout(() => {
                        if (!selectionComplete && this.pollingInterval) {
                            clearInterval(this.pollingInterval);
                            this.pollingInterval = null;
                            console.log('Picker closed quickly but no selection detected - likely cancelled');
                            this.updateStatus('Photo selection cancelled');
                        }
                    }, 15000); // Give 15 seconds for quick autoclose scenarios
                }
            }
        }, 2000); // Check less frequently to avoid spam

        // Poll for session completion more aggressively
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/google-photos/session-status');
                const data = await response.json();
                
                console.log('Session status check:', data.session?.mediaItemsSet ? 'COMPLETE' : 'pending');
                
                if (data.session?.mediaItemsSet) {
                    // Selection complete!
                    console.log('Selection detected - marking complete');
                    selectionComplete = true;
                    clearInterval(this.pollingInterval);
                    clearInterval(checkClosed);
                    this.pollingInterval = null;
                    
                    if (!pickerWindow.closed) {
                        pickerWindow.close();
                    }
                    
                    await this.handleSelectionComplete();
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000); // Poll every 2 seconds - reasonable balance of responsiveness and server load
    }

    async handleSelectionComplete() {
        this.updateStatus('Photos selected! Processing...', 'processing');
        
        try {
            // Get selected photos
            const response = await fetch('/api/google-photos/selected-photos');
            
            if (!response.ok) {
                throw new Error(`Failed to get selected photos: ${response.status}`);
            }
            
            const data = await response.json();
            const mediaItems = data.pickedMediaItems || data.mediaItems || [];
            
            console.log('Selected photos response:', data);
            console.log('Media items found:', mediaItems.length);
            
            if (mediaItems.length === 0) {
                this.updateStatus('No photos were selected');
                return;
            }
            
            this.updateStatus(`Downloading ${mediaItems.length} photos...`, 'processing');
            
            // Auto-download selected photos
            await this.downloadSelectedPhotos(mediaItems);
            
        } catch (error) {
            console.error('Selection processing failed:', error);
            this.updateStatus(`Processing error: ${error.message}`, 'error');
        }
    }

    async downloadSelectedPhotos(mediaItems) {
        try {
            // Add placeholder thumbnails immediately
            this.addPlaceholderThumbnails(mediaItems);
            
            // Call download endpoint
            const response = await fetch('/api/google-photos/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mediaItems })
            });
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.downloaded_count > 0) {
                this.updateStatus(
                    `Successfully downloaded ${result.downloaded_count} photos! Converting for display...`, 
                    'success'
                );
                
                // Refresh main images grid
                if (window.refreshImages) {
                    window.refreshImages();
                }
                
                // Auto-hide after success
                setTimeout(() => {
                    this.updateStatus('Ready to select more photos');
                }, 3000);
                
            } else {
                this.updateStatus('No photos were downloaded', 'error');
            }
            
        } catch (error) {
            console.error('Download failed:', error);
            this.updateStatus(`Download error: ${error.message}`, 'error');
        }
    }

    addPlaceholderThumbnails(mediaItems) {
        const thumbsList = document.getElementById('thumbList');
        if (!thumbsList) return;

        mediaItems.forEach(item => {
            const filename = item.mediaFile?.filename || `photo_${item.id.substring(0, 8)}.jpg`;
            const placeholder = document.createElement('div');
            placeholder.className = 'thumb placeholder-thumb';
            placeholder.id = `placeholder-${filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
            placeholder.innerHTML = `
                <div class="placeholder-content">
                    <div class="placeholder-spinner"></div>
                    <div class="placeholder-text">Converting...</div>
                    <div class="placeholder-filename">${filename}</div>
                </div>
            `;
            
            // Add to top of thumb list (newest first)
            thumbsList.insertBefore(placeholder, thumbsList.firstChild);
        });
    }
}

// Initialize when page loads
let simpleGooglePhotos;
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing SimpleGooglePhotos...');
    simpleGooglePhotos = new SimpleGooglePhotos();
});