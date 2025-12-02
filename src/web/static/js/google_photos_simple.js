class SimpleGooglePhotos {
    constructor() {
        this.authenticated = false;
        this.currentSession = null;
        this.pollingInterval = null;
        
        // TODO: Sync whitelist with backend configuration
        this.whitelistedDomains = [
            'epaper.whirlwind.family' // TODO: Wire in from terraform output
        ];
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkDomainAndAuth();
    }

    setupEventListeners() {
        const loginBtn = document.getElementById('loginBtn');
        loginBtn?.addEventListener('click', () => this.handleAuth());

        const logoutBtn = document.getElementById('logoutBtn');
        logoutBtn?.addEventListener('click', () => this.handleDisconnect());

        const openPickerBtn = document.getElementById('openPickerBtn');
        openPickerBtn?.addEventListener('click', () => this.openPhotoPicker());
    }

    isWhitelistedDomain() {
        const hostname = window.location.hostname;
        return this.whitelistedDomains.some(domain => {
            if (domain === hostname) return true;
            if (domain.startsWith('.') && hostname.endsWith(domain)) return true;
            return false;
        });
    }

    buildRedirectUrl(domain) {
        const protocol = window.location.protocol;
        const port = window.location.port ? `:${window.location.port}` : '';
        return `${protocol}//${domain}${port}?tab=photos`;
    }

    async checkDomainAndAuth() {
        if (!this.isWhitelistedDomain()) {
            this.showDomainRedirect();
        } else {
            await this.checkAuthStatus();
        }
    }

    showDomainRedirect() {
        const authStatusText = document.getElementById('authStatusText');
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const pickerSection = document.getElementById('pickerSection');
        const pickerStatus = document.getElementById('pickerStatus');
        
        const redirectDomain = this.whitelistedDomains[0];
        const redirectUrl = this.buildRedirectUrl(redirectDomain);
        
        authStatusText.textContent = 'Google Photos requires a whitelisted domain';
        loginBtn.textContent = `Redirect to ${redirectDomain}`;
        loginBtn.style.display = 'inline-block';
        loginBtn.onclick = () => window.location.href = redirectUrl;
        logoutBtn.style.display = 'none';
        pickerSection.style.display = 'none';
        pickerStatus.style.display = 'none';
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

        if (authData.authenticated) {
            authStatusText.textContent = `Signed in as ${authData.user?.email || 'Google user'}`;
            loginBtn.style.display = 'none';
            loginBtn.onclick = null;
            logoutBtn.style.display = 'inline-block';
            pickerSection.style.display = 'block';
            pickerStatus.style.display = 'block';
            this.updateStatus('Ready to select photos');
        } else {
            authStatusText.textContent = 'Not signed in to Google Photos';
            loginBtn.textContent = 'Sign In with Google';
            loginBtn.style.display = 'inline-block';
            loginBtn.onclick = null;
            logoutBtn.style.display = 'none';
            pickerSection.style.display = 'none';
            pickerStatus.style.display = 'none';
            this.updateStatus('Sign in required');
        }
    }

    updateStatus(message, type = 'info') {
        const statusElement = document.getElementById('pickerStatusText');
        const statusContainer = document.getElementById('pickerStatus');
        
        if (statusElement) {
            statusElement.textContent = message;
        }
        
        if (statusContainer) {
            statusContainer.className = 'picker-status';
            if (type !== 'info') {
                statusContainer.classList.add(type);
            }
        }
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
        
        const checkClosed = setInterval(() => {
            if (pickerWindow.closed && !selectionComplete) {
                clearInterval(checkClosed);
                const elapsedTime = Date.now() - startTime;
                const minTimeForSelection = 10000;
                const waitTimeAfterClose = elapsedTime > minTimeForSelection ? 10000 : 15000;
                
                setTimeout(() => {
                    if (!selectionComplete && this.pollingInterval) {
                        clearInterval(this.pollingInterval);
                        this.pollingInterval = null;
                        this.updateStatus('Photo selection cancelled');
                    }
                }, waitTimeAfterClose);
            }
        }, 2000);

        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/google-photos/session-status');
                const data = await response.json();
                
                if (data.session?.mediaItemsSet) {
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
        }, 2000);
    }

    async handleSelectionComplete() {
        this.updateStatus('Photos selected! Processing...', 'processing');
        
        try {
            const response = await fetch('/api/google-photos/selected-photos');
            if (!response.ok) {
                throw new Error(`Failed to get selected photos: ${response.status}`);
            }
            
            const data = await response.json();
            const mediaItems = data.pickedMediaItems || data.mediaItems || [];
            
            if (mediaItems.length === 0) {
                this.updateStatus('No photos were selected');
                return;
            }
            
            this.updateStatus(`Downloading ${mediaItems.length} photos...`, 'processing');
            await this.downloadSelectedPhotos(mediaItems);
        } catch (error) {
            console.error('Selection processing failed:', error);
            this.updateStatus(`Processing error: ${error.message}`, 'error');
        }
    }

    async downloadSelectedPhotos(mediaItems) {
        try {
            this.addPlaceholderThumbnails(mediaItems);
            
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
                
                if (window.refreshImages) {
                    window.refreshImages();
                }
                
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

let simpleGooglePhotos;
document.addEventListener('DOMContentLoaded', () => {
    simpleGooglePhotos = new SimpleGooglePhotos();
});