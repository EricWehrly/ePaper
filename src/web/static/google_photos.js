class GooglePhotosManager {
    constructor() {
        this.selectedPhotos = new Set();
        this.currentAlbum = null;
        this.currentTab = 'recent';
        this.currentPage = 0;
        this.pageSize = 20;
        this.albums = [];
        this.init();
    }

    async init() {
        console.log('GooglePhotosManager initializing...');
        this.setupEventListeners();
        await this.checkNgrokRedirect();
        await this.checkAuthStatus();
    }

    async checkNgrokRedirect() {
        // Only check if we're on raspberrypi.local and not authenticated
        if (!window.location.hostname.includes('raspberrypi.local')) return;
        
        try {
            // Check if ngrok URL is available and if we should redirect
            const response = await fetch('/api/google-photos/ngrok-info');
            if (response.ok) {
                const data = await response.json();
                if (data.ngrok_url && data.should_redirect) {
                    this.showNgrokBanner(data.ngrok_url);
                }
            }
        } catch (error) {
            console.log('Ngrok check failed (expected if not configured):', error);
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

    setupEventListeners() {
        console.log('Setting up event listeners...');
        const toggleBtn = document.getElementById('toggleGooglePhotos');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleSection());
        }

        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.handleAuth());
        }

        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleAuth());
        }

        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadSelectedPhotos());
        }

        const clearSelectionBtn = document.getElementById('clearSelectionBtn');
        if (clearSelectionBtn) {
            clearSelectionBtn.addEventListener('click', () => this.clearSelection());
        }

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
    }

    switchTab(tabName) {
        console.log('Switching to tab:', tabName);
        this.currentTab = tabName;
        
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Show/hide content areas
        const recentTab = document.getElementById('recentTab');
        const albumsTab = document.getElementById('albumsTab');
        
        if (tabName === 'albums') {
            if (recentTab) recentTab.style.display = 'none';
            if (albumsTab) albumsTab.style.display = 'block';
        } else {
            // Recent photos tab
            if (recentTab) recentTab.style.display = 'block';
            if (albumsTab) albumsTab.style.display = 'none';
        }
        
        this.loadContent();
    }

    async loadContent() {
        if (!this.isAuthenticated) {
            console.log('Not authenticated, showing placeholder content');
            this.showPlaceholderContent();
            return;
        }
        
        // For now, just show that we're trying to load
        console.log('Would load content for tab:', this.currentTab);
        
        // Actually load the content based on the tab
        if (this.currentTab === 'recent') {
            await this.loadRecentPhotos();
        } else if (this.currentTab === 'albums') {
            await this.loadAlbums();
        }
    }

    async loadRecentPhotos() {
        console.log('Loading photos using Picker API...');
        const recentPhotosGrid = document.getElementById('recentPhotosGrid');
        
        if (!recentPhotosGrid) return;
        
        // Show picker interface instead of loading photos directly
        recentPhotosGrid.innerHTML = `
            <div class="picker-interface">
                <div class="picker-info">
                    <h4>Select Photos & Albums from Google Photos</h4>
                    <p>Click the button below to open Google Photos and select individual photos or entire albums to download.</p>
                    <button id="openPickerBtn" class="ctl-btn control">Select Photos & Albums</button>
                </div>
                <div id="pickerStatus" style="display: none;">
                    <p>Waiting for photo selection...</p>
                    <div class="loading-spinner"></div>
                    <button id="checkSelectionBtn" class="ctl-btn control" style="margin-top: 10px;">Check Selection</button>
                </div>
                <div id="selectedPhotosContainer" style="display: none;">
                    <h4>Selected Items</h4>
                    <div id="selectedPhotosGrid" class="photos-grid"></div>
                    <button id="downloadSelectedBtn" class="ctl-btn control">Download Selected Items</button>
                </div>
            </div>
        `;
        
        // Add event listener for picker button
        const openPickerBtn = document.getElementById('openPickerBtn');
        if (openPickerBtn) {
            openPickerBtn.addEventListener('click', () => this.openPhotoPicker());
        }
        
        // Add event listener for download button
        const downloadBtn = document.getElementById('downloadSelectedBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadSelectedPhotos());
        }
        
        // Add event listener for manual check button
        const checkBtn = document.getElementById('checkSelectionBtn');
        if (checkBtn) {
            checkBtn.addEventListener('click', () => this.manualCheckSelection());
        }
    }

    async loadAlbums() {
        console.log('Showing album selection instructions...');
        const albumsList = document.getElementById('albumsList');
        
        if (!albumsList) return;
        
        albumsList.innerHTML = `
            <div class="picker-info">
                <h4>📁 Album Selection</h4>
                <p><strong>Albums are selected using the same picker interface as photos.</strong></p>
                <p>To select albums:</p>
                <ol>
                    <li>Go to the <strong>"Recent Photos"</strong> tab</li>
                    <li>Click <strong>"Select Photos & Albums"</strong></li>
                    <li>In the Google Photos picker, you can select both:</li>
                    <ul>
                        <li>📷 Individual photos</li>
                        <li>📁 Entire albums</li>
                    </ul>
                    <li>Click "Done" when finished</li>
                </ol>
                <p><em>Both photos and albums will be downloaded and converted for your e-Paper display.</em></p>
            </div>
        `;
    }

    async openPhotoPicker() {
        console.log('Opening Google Photos picker...');
        
        try {
            // Create a picker session
            const response = await fetch('/api/google-photos/create-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to create picker session');
            }
            
            const result = await response.json();
            const session = result.session;
            
            console.log('Created picker session:', session.id);
            
            // Hide picker button and show status
            const openPickerBtn = document.getElementById('openPickerBtn');
            const pickerStatus = document.getElementById('pickerStatus');
            
            if (openPickerBtn) {
                openPickerBtn.style.display = 'none';
                console.log('Hidden picker button');
            } else {
                console.error('Could not find openPickerBtn element');
            }
            
            if (pickerStatus) {
                pickerStatus.style.display = 'block';
                console.log('Showing picker status div (should include Check Selection button)');
            } else {
                console.error('Could not find pickerStatus element');
            }
            
            // Open the picker in a new window
            const pickerWindow = window.open(
                session.pickerUri,
                'GooglePhotosPicker',
                'width=800,height=600,scrollbars=yes,resizable=yes'
            );
            
            // Start polling for completion
            this.pollPickerSession(session.id, pickerWindow);
            
        } catch (error) {
            console.error('Failed to open picker:', error);
            alert('Failed to open photo picker: ' + error.message);
        }
    }

    async pollPickerSession(sessionId, pickerWindow) {
        const maxAttempts = 120; // 10 minutes at 5-second intervals
        let attempts = 0;
        
        const poll = async () => {
            attempts++;
            console.log(`Polling attempt ${attempts}/${maxAttempts} for session ${sessionId}`);
            
            try {
                const response = await fetch('/api/google-photos/session-status');
                console.log('Session status response:', response.status, response.statusText);
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Session status result:', result);
                    const session = result.session;
                    
                    if (session && session.mediaItemsSet) {
                        // User completed selection
                        console.log('Photo selection completed!');
                        if (pickerWindow && !pickerWindow.closed) {
                            pickerWindow.close();
                        }
                        
                        // Hide status and load selected photos
                        document.getElementById('pickerStatus').style.display = 'none';
                        await this.loadSelectedPhotos();
                        return;
                    } else {
                        console.log('No selection detected yet, mediaItemsSet:', session ? session.mediaItemsSet : 'no session');
                    }
                } else {
                    const errorText = await response.text();
                    console.log('Session status error:', errorText);
                }
                
                // Check if picker window was closed (but be more lenient about detection)
                if (pickerWindow && pickerWindow.closed && attempts > 3) {
                    console.log('Picker window was closed after', attempts, 'attempts');
                    
                    // Do one final check for completed selection before giving up
                    try {
                        const finalResponse = await fetch('/api/google-photos/session-status');
                        if (finalResponse.ok) {
                            const finalResult = await finalResponse.json();
                            if (finalResult.session && finalResult.session.mediaItemsSet) {
                                console.log('Selection detected after window closed!');
                                document.getElementById('pickerStatus').style.display = 'none';
                                await this.loadSelectedPhotos();
                                return;
                            }
                        }
                    } catch (e) {
                        console.log('Final selection check failed:', e);
                    }
                    
                    // No selection found, but keep the UI open for manual checking
                    console.log('Window closed but no selection detected - keeping UI open for manual checking');
                    // Don't hide the status, let user manually check
                    return;
                    document.getElementById('openPickerBtn').style.display = 'block';
                    return;
                }
                
                // Continue polling if under limit
                if (attempts < maxAttempts) {
                    setTimeout(poll, 5000); // Poll every 5 seconds
                } else {
                    console.log('Polling timeout reached');
                    document.getElementById('pickerStatus').style.display = 'none';
                    document.getElementById('openPickerBtn').style.display = 'block';
                    alert('Photo selection timed out. Please try again.');
                }
                
            } catch (error) {
                console.error('Error polling session:', error);
                setTimeout(poll, 5000); // Retry on error
            }
        };
        
        // Start polling
        setTimeout(poll, 2000); // Initial delay
    }

    async manualCheckSelection() {
        console.log('Manually checking for selection...');
        try {
            const response = await fetch('/api/google-photos/session-status');
            console.log('Manual check response:', response.status, response.statusText);
            
            if (response.ok) {
                const result = await response.json();
                console.log('Manual check result:', result);
                
                if (result.session && result.session.mediaItemsSet) {
                    console.log('Selection found!');
                    document.getElementById('pickerStatus').style.display = 'none';
                    await this.loadSelectedPhotos();
                } else {
                    console.log('No selection found yet, mediaItemsSet:', result.session ? result.session.mediaItemsSet : 'no session');
                    alert('No photos selected yet. Please try selecting photos in the picker window.');
                }
            } else {
                const errorText = await response.text();
                console.log('Manual check failed:', response.status, errorText);
                alert('Failed to check selection status');
            }
        } catch (error) {
            console.error('Manual check failed:', error);
            alert('Failed to check selection: ' + error.message);
        }
    }

    async loadSelectedPhotos() {
        console.log('Loading selected photos...');
        
        try {
            const response = await fetch('/api/google-photos/selected-photos');
            
            if (!response.ok) {
                throw new Error('Failed to load selected photos');
            }
            
            const result = await response.json();
            
            // Handle Picker API limitation
            if (result.error && result.error === 'Picker API Limitation') {
                console.log('Picker API limitation encountered:', result.details);
                this.showPickerLimitation();
                return;
            }
            
            const photos = result.pickedMediaItems || [];
            const albums = result.pickedAlbums || [];
            
            console.log('Loaded selected items:', photos.length, 'photos,', albums.length, 'albums');
            
            // Show selected photos container
            const container = document.getElementById('selectedPhotosContainer');
            const grid = document.getElementById('selectedPhotosGrid');
            
            if (container && grid) {
                container.style.display = 'block';
                
                // Update container title to reflect both photos and albums
                const title = container.querySelector('h4');
                if (title) {
                    title.textContent = `Selected Items (${photos.length} photos, ${albums.length} albums)`;
                }
                
                this.renderSelectedItems(photos, albums, 'selectedPhotosGrid');
            }
            
        } catch (error) {
            console.error('Failed to load selected photos:', error);
            alert('Failed to load selected photos: ' + error.message);
        }
    }

    showPickerLimitation() {
        console.log('Showing Picker API limitation message');
        
        // Show selected photos container with limitation message
        const container = document.getElementById('selectedPhotosContainer');
        const grid = document.getElementById('selectedPhotosGrid');
        
        if (container && grid) {
            container.style.display = 'block';
            
            // Update container title
            const title = container.querySelector('h4');
            if (title) {
                title.textContent = 'Photo Selection Completed ✅';
            }
            
            // Show limitation message
            grid.innerHTML = `
                <div class="picker-limitation-message">
                    <div class="limitation-icon">📸</div>
                    <h3>Photos Selected Successfully!</h3>
                    <p>You have successfully selected photos using Google Photos Picker.</p>
                    <div class="limitation-explanation">
                        <p><strong>Technical Note:</strong> Due to the current design of Google's Photos Picker API, 
                        we cannot display the specific photos you selected in this interface. However, your 
                        selection was successful and has been recorded.</p>
                        <p>This is a limitation of Google's Picker API design, not our application.</p>
                    </div>
                    <div class="next-steps">
                        <h4>What's Next?</h4>
                        <p>You can now continue to select more photos or return to the main interface.</p>
                        <button id="selectMorePhotosBtn" class="ctl-btn control">Select More Photos</button>
                    </div>
                </div>
            `;
            
            // Add event listener to "Select More Photos" button
            const selectMoreBtn = document.getElementById('selectMorePhotosBtn');
            if (selectMoreBtn) {
                selectMoreBtn.addEventListener('click', () => {
                    container.style.display = 'none';
                    document.getElementById('pickerStatus').style.display = 'none';
                    document.getElementById('openPickerBtn').style.display = 'block';
                });
            }
        }
    }

    async downloadSelectedPhotos() {
        console.log('Downloading selected photos...');
        
        try {
            const response = await fetch('/api/google-photos/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to download photos');
            }
            
            const result = await response.json();
            
            console.log('Download result:', result);
            
            let message = '';
            if (result.downloaded_count > 0) {
                message = `Downloaded ${result.downloaded_count} items successfully!`;
                if (result.failed_count > 0) {
                    message += ` (${result.failed_count} failed)`;
                }
            } else {
                message = 'No items were downloaded. Please check the logs for details.';
            }
            
            alert(message);
            
            // Refresh the main images grid
            if (window.refreshImages) {
                window.refreshImages();
            }
            
        } catch (error) {
            console.error('Failed to download photos:', error);
            alert('Failed to download photos: ' + error.message);
        }
    }

    async loadAlbumsOld() {
        // This method is deprecated - albums are now selected via the Picker API
        console.log('Albums are selected via Picker API...');
        const albumsList = document.getElementById('albumsList');
        if (!albumsList) return;
        
        albumsList.innerHTML = `
            <div class="picker-info">
                <h4>Photo & Album Selection</h4>
                <p>Albums are now selected using the Google Photos Picker interface.</p>
                <p>Use the "Recent Photos" tab to open the picker and select both photos and albums.</p>
            </div>
        `;
    }

    renderSelectedItems(photos, albums, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        // Render albums first
        albums.forEach(album => {
            const albumElement = document.createElement('div');
            albumElement.className = 'photo-item album-item';
            albumElement.innerHTML = `
                <div class="album-cover">
                    <img src="${album.coverPhotoBaseUrl || '/static/album-placeholder.png'}=w200-h200-c" alt="${album.title}" loading="lazy">
                    <div class="album-badge">📁 Album</div>
                </div>
                <div class="photo-info">
                    <div class="album-title">${album.title}</div>
                    <div class="album-count">${album.mediaItemsCount} items</div>
                </div>
            `;
            container.appendChild(albumElement);
        });
        
        // Render individual photos
        photos.forEach(photo => {
            const photoElement = document.createElement('div');
            photoElement.className = 'photo-item';
            photoElement.innerHTML = `
                <img src="${photo.baseUrl}=w200-h200-c" alt="${photo.filename || 'Photo'}" loading="lazy">
                <div class="photo-info">
                    <div class="photo-filename">${photo.filename || 'Photo'}</div>
                </div>
            `;
            container.appendChild(photoElement);
        });
    }

    renderPhotoGrid(photos, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        photos.forEach(photo => {
            const photoElement = document.createElement('div');
            photoElement.className = 'photo-item';
            photoElement.innerHTML = `
                <img src="${photo.baseUrl}=w200-h200-c" alt="${photo.filename || 'Photo'}" loading="lazy">
                <div class="photo-overlay">
                    <div class="photo-select-btn" data-photo-id="${photo.id}">
                        <span class="checkmark">✓</span>
                    </div>
                </div>
            `;
            
            // Add click handler for selection
            const selectBtn = photoElement.querySelector('.photo-select-btn');
            selectBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePhotoSelection(photo.id, photoElement);
            });
            
            container.appendChild(photoElement);
        });
    }

    renderAlbumsList(albums) {
        const container = document.getElementById('albumsList');
        if (!container) return;
        
        container.innerHTML = '';
        
        albums.forEach(album => {
            const albumElement = document.createElement('div');
            albumElement.className = 'album-item';
            albumElement.innerHTML = `
                <div class="album-cover">
                    <img src="${album.coverPhotoBaseUrl || ''}=w200-h200-c" alt="${album.title}" loading="lazy">
                </div>
                <div class="album-info">
                    <h4>${album.title}</h4>
                    <p>${album.mediaItemsCount || 0} photos</p>
                </div>
            `;
            
            albumElement.addEventListener('click', () => {
                this.openAlbum(album);
            });
            
            container.appendChild(albumElement);
        });
    }

    togglePhotoSelection(photoId, photoElement) {
        if (this.selectedPhotos.has(photoId)) {
            this.selectedPhotos.delete(photoId);
            photoElement.classList.remove('selected');
        } else {
            this.selectedPhotos.add(photoId);
            photoElement.classList.add('selected');
        }
        
        this.updateSelectedCount();
    }

    updateSelectedCount() {
        const countElement = document.getElementById('selectedCount');
        const selectedSection = document.getElementById('selectedPhotos');
        
        if (countElement) {
            countElement.textContent = this.selectedPhotos.size;
        }
        
        if (selectedSection) {
            selectedSection.style.display = this.selectedPhotos.size > 0 ? 'block' : 'none';
        }
    }

    async openAlbum(album) {
        console.log('Opening album:', album.title);
        // TODO: Implement album photo loading
        // This would load photos from the specific album
    }

    async downloadSelectedPhotos() {
        if (this.selectedPhotos.size === 0) {
            alert('Please select some photos first');
            return;
        }

        const downloadBtn = document.getElementById('downloadBtn');
        const originalText = downloadBtn.textContent;
        
        try {
            downloadBtn.textContent = 'Downloading...';
            downloadBtn.disabled = true;

            const photoIds = Array.from(this.selectedPhotos);
            console.log('Downloading photos:', photoIds);

            const response = await fetch('/api/google-photos/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    photo_ids: photoIds
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('Download result:', result);

            // Show success message
            alert(`Successfully downloaded ${result.downloaded_count} photos!`);
            
            // Clear selection
            this.clearSelection();
            
            // Trigger a refresh of the main file list
            if (window.refreshFileList) {
                window.refreshFileList();
            }

        } catch (error) {
            console.error('Download failed:', error);
            alert('Download failed: ' + error.message);
        } finally {
            downloadBtn.textContent = originalText;
            downloadBtn.disabled = false;
        }
    }

    clearSelection() {
        this.selectedPhotos.clear();
        
        // Remove selected class from all photo items
        document.querySelectorAll('.photo-item.selected').forEach(item => {
            item.classList.remove('selected');
        });
        
        this.updateSelectedCount();
    }

    showPlaceholderContent() {
        const recentGrid = document.getElementById('recentPhotosGrid');
        const albumsList = document.getElementById('albumsList');
        
        if (recentGrid) {
            recentGrid.innerHTML = '<div class="loading-placeholder">Please authenticate with Google Photos to see recent photos</div>';
        }
        
        if (albumsList) {
            albumsList.innerHTML = '<div class="loading-placeholder">Please authenticate with Google Photos to see albums</div>';
        }
    }

    async checkAuthStatus() {
        console.log('Checking auth status...');
        try {
            const response = await fetch('/api/google-photos/status');
            const data = await response.json();
            this.isAuthenticated = data.authenticated;
            this.updateAuthUI(data);
        } catch (error) {
            console.error('Failed to check auth status:', error);
            this.isAuthenticated = false;
        }
    }

    updateAuthUI(authData) {
        console.log('Updating auth UI:', authData);
        const statusEl = document.getElementById('authStatusText');
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        
        if (!statusEl) {
            console.warn('authStatusText element not found');
            return;
        }
        
        if (authData.authenticated) {
            statusEl.textContent = 'Connected to Google Photos';
            statusEl.style.color = 'green';
            if (loginBtn) loginBtn.style.display = 'none';
            if (logoutBtn) logoutBtn.style.display = 'inline-block';
            
            // Load initial content if authenticated
            this.loadContent();
        } else {
            statusEl.textContent = 'Not connected to Google Photos';
            statusEl.style.color = 'red';
            if (loginBtn) loginBtn.style.display = 'inline-block';
            if (logoutBtn) logoutBtn.style.display = 'none';
            
            // Show placeholder content
            this.showPlaceholderContent();
        }
    }

    async handleAuth() {
        console.log('Handling auth...');
        if (this.isAuthenticated) {
            await this.handleDisconnect();
        } else {
            console.log('Connecting...');
            window.location.href = '/api/google-photos/auth';
        }
    }

    async handleDisconnect() {
        console.log('Disconnecting from Google Photos...');
        try {
            const response = await fetch('/api/google-photos/disconnect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Disconnected successfully:', result.message);
                
                // Update authentication state
                this.isAuthenticated = false;
                
                // Refresh the authentication status
                await this.checkAuthStatus();
                
                // Hide Google Photos content
                const content = document.getElementById('googlePhotosContent');
                if (content) content.style.display = 'none';
                
                // Show success message
                alert('Successfully signed out of Google Photos');
                
            } else {
                const error = await response.json();
                console.error('Disconnect failed:', error);
                alert('Failed to sign out: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Disconnect request failed:', error);
            alert('Failed to sign out: Network error');
        }
    }

    toggleSection() {
        console.log('Toggling Google Photos section...');
        const section = document.getElementById('googlePhotosSection');
        const content = document.getElementById('googlePhotosContent');
        const btn = document.getElementById('toggleGooglePhotos');
        
        if (!section || !btn) {
            console.warn('Section or button not found');
            return;
        }
        
        if (section.style.display === 'none') {
            section.style.display = 'block';
            if (content) content.style.display = 'block';
            btn.textContent = 'Hide Google Photos';
        } else {
            section.style.display = 'none';
            if (content) content.style.display = 'none';
            btn.textContent = 'Google Photos';
        }
    }
}

// Initialize when page loads
let googlePhotos;
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing GooglePhotosManager...');
    googlePhotos = new GooglePhotosManager();
});
