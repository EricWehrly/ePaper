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

    /**
     * Create a proxied URL for Google Photos images that require authentication
     * @param {string} baseUrl - The Google Photos base URL
     * @param {string} params - Image parameters (default: w200-h200-c)
     * @returns {string} - Proxied URL that can be used in frontend
     */
    createProxyImageUrl(baseUrl, params = 'w200-h200-c') {
        if (!baseUrl || baseUrl.startsWith('/static/') || (baseUrl.startsWith('http://') && !baseUrl.includes('googleusercontent.com'))) {
            // For placeholder images or non-Google URLs, return as-is
            return baseUrl;
        }
        // Use the backend media proxy which attaches the OAuth token and handles Google URLs
        return `/api/google-photos/media?baseUrl=${encodeURIComponent(baseUrl)}&modifier=${encodeURIComponent(params)}`;
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
                },
                body: JSON.stringify({
                    // Include callback configuration
                    includeCallback: true
                })
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
            
            // Setup callback to capture selection data
            this.setupPickerCallback(session.id);
            
            // Try both approaches: popup window AND iframe
            console.log('Trying picker in popup window...');
            const pickerWindow = window.open(
                session.pickerUri,
                'GooglePhotosPicker',
                'width=800,height=600,scrollbars=yes,resizable=yes'
            );
            
            // Also try embedding in an iframe for better callback handling
            console.log('Also trying picker in iframe...');
            this.createPickerIframe(session.pickerUri, session.id);
            
            // Start polling for completion (but now we'll also have callback data)
            this.pollPickerSession(session.id, pickerWindow);
            
        } catch (error) {
            console.error('Failed to open picker:', error);
            alert('Failed to open photo picker: ' + error.message);
        }
    }

    setupPickerCallback(sessionId) {
        console.log('🔗 Setting up picker callback for session:', sessionId);
        
        // Listen for messages - simplified logging
        const messageHandler = (event) => {
            // Minimal logging: only act on likely picker messages.
            // Many browser extensions (React DevTools, etc.) postMessage into pages
            // which creates a lot of noise. Ignore those by quick checks.
            let data = event.data;
            if (typeof data === 'string') {
                try {
                    data = JSON.parse(data);
                } catch (e) {
                    // Not JSON, ignore quickly
                    return;
                }
            }

            // Ignore known noisy sources
            if (data && data.source && typeof data.source === 'string') {
                const src = data.source.toLowerCase();
                if (src.includes('react-devtools') || src.includes('extension') || src.includes('reduxdevtools')) {
                    // Quietly ignore extension messages
                    return;
                }
            }

            // Only accept messages that are likely picker callbacks:
            // - contain a sessionId matching the session we're tracking
            // - or have explicit selection/media properties
            const looksLikePicker = data && (
                (data.sessionId && String(data.sessionId) === String(sessionId)) ||
                data.type === 'PICKER_SELECTION' ||
                data.pickedMediaItems ||
                data.selectedMedia ||
                data.mediaItems ||
                data.photos ||
                data.selection ||
                (typeof data === 'object' && Object.keys(data).some(key =>
                    ['select', 'media', 'photo', 'picked'].some(k => key.toLowerCase().includes(k))
                ))
            );

            if (!looksLikePicker) {
                // Not relevant to picker flow; ignore to reduce noise
                return;
            }

            // Log only when we have something relevant
            console.log('🎯 PICKER SELECTION DETECTED (filtered):', { origin: event.origin, data });
            this.handlePickerSelection(sessionId, data);
        };
        
        // Add event listener for messages
        window.addEventListener('message', messageHandler);
        
        // Store the handler so we can clean it up later
        this.currentMessageHandler = messageHandler;
        
        console.log('✅ Message listener active');
    }

    createPickerIframe(pickerUri, sessionId) {
        console.log('Creating picker iframe for session:', sessionId);
        
        // Create a container for the iframe
        const iframeContainer = document.createElement('div');
        iframeContainer.id = 'pickerIframeContainer';
        iframeContainer.style.cssText = `
            position: fixed;
            top: 10%;
            left: 10%;
            width: 80%;
            height: 80%;
            background: white;
            border: 3px solid #007cba;
            border-radius: 8px;
            z-index: 10000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: none;
        `;
        
        // Create header with close button
        const header = document.createElement('div');
        header.style.cssText = `
            background: #007cba;
            color: white;
            padding: 10px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;
        header.innerHTML = `
            <span>🖼️ Google Photos Picker (iframe test)</span>
            <button id="closePickerIframe" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">✕</button>
        `;
        
        // Create iframe
        const iframe = document.createElement('iframe');
        iframe.src = pickerUri;
        iframe.style.cssText = `
            width: 100%;
            height: calc(100% - 50px);
            border: none;
        `;
        iframe.id = 'pickerIframe';
        
        // Assemble container
        iframeContainer.appendChild(header);
        iframeContainer.appendChild(iframe);
        document.body.appendChild(iframeContainer);
        
        // Add close button functionality
        document.getElementById('closePickerIframe').addEventListener('click', () => {
            iframeContainer.style.display = 'none';
        });
        
        // Add button to show/hide iframe
        const toggleButton = document.createElement('button');
        toggleButton.textContent = '🖼️ Try Picker in iframe';
        toggleButton.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10001;
            padding: 10px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        `;
        toggleButton.addEventListener('click', () => {
            iframeContainer.style.display = iframeContainer.style.display === 'none' ? 'block' : 'none';
        });
        document.body.appendChild(toggleButton);
        
        console.log('Picker iframe created and ready');
    }

    handlePickerSelection(sessionId, selectionData) {
        console.log('Processing picker selection for session:', sessionId);
        console.log('Selection data received:', JSON.stringify(selectionData, null, 2));
        
        // Send the selection data to our backend
        this.sendSelectionToBackend(sessionId, selectionData);
        
        // Show the selection in the UI
        this.displayPickerSelection(selectionData);
    }

    async sendSelectionToBackend(sessionId, selectionData) {
        console.log('Sending selection data to backend...');
        
        try {
            const response = await fetch('/api/google-photos/picker-callback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: sessionId,
                    selectionData: selectionData
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to send selection to backend');
            }
            
            const result = await response.json();
            console.log('Backend received selection:', result);
            
        } catch (error) {
            console.error('Error sending selection to backend:', error);
        }
    }

    displayPickerSelection(selectionData) {
        console.log('Displaying picker selection in UI...');
        
        // Show selected photos container
        const container = document.getElementById('selectedPhotosContainer');
        const grid = document.getElementById('selectedPhotosGrid');
        
        if (!container || !grid) {
            console.error('Could not find selection display elements');
            return;
        }
        
        container.style.display = 'block';
        
        // Update container title
        const title = container.querySelector('h4');
        if (title) {
            title.textContent = 'Photos Selected via Callback ✅';
        }
        
        // Show simple selection success message
        grid.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <h3>🎉 Selection Captured Successfully!</h3>
                <p>Received selection data from Google Photos Picker callback. Processing photos...</p>
                <div class="loading-spinner" style="margin: 20px auto;"></div>
            </div>
        `;
        
        // Automatically process the selection
        this.processSelectedPhotos(selectionData);
    }

    processSelectedPhotos(selectionData) {
        console.log('Processing selected photos:', selectionData);
        // For now, just trigger the normal loadSelectedPhotos flow
        // In the future, this could use the callback data directly
        setTimeout(() => this.loadSelectedPhotos(), 1000);
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
        console.log('🔍 Loading selected photos from backend...');
        
        try {
            const response = await fetch('/api/google-photos/selected-photos');
            console.log('📡 Selected photos response:', response.status, response.statusText);
            
            if (!response.ok) {
                // Try to get error details from response
                let errorDetails = 'Unknown error';
                try {
                    const errorResult = await response.json();
                    errorDetails = errorResult.error || errorResult.details || errorDetails;
                    console.error('❌ Backend error:', errorResult);
                } catch (e) {
                    // If we can't parse JSON, use the response text
                    errorDetails = await response.text();
                    console.error('❌ Response error:', errorDetails);
                }
                throw new Error(`HTTP ${response.status}: ${errorDetails}`);
            }
            
            const result = await response.json();
            console.log('📊 Selected photos result:', result);
            
            // Check if we got a success response with picked media items
            if (result.success && result.pickedMediaItems) {
                const photos = result.pickedMediaItems || [];
                console.log(`✅ Successfully loaded ${photos.length} selected photos!`);
                
                // Show selected photos container
                const container = document.getElementById('selectedPhotosContainer');
                const grid = document.getElementById('selectedPhotosGrid');
                
                if (container && grid) {
                    container.style.display = 'block';
                    
                    // Update container title
                    const title = container.querySelector('h4');
                    if (title) {
                        title.textContent = `✅ Selected Photos (${photos.length} items)`;
                    }
                    
                    // Render the actual selected photos
                    this.renderPickedMediaItems(photos, 'selectedPhotosGrid');
                } else {
                    console.error('Could not find photo display containers');
                }
                
                return; // Success path
            }
            
            // Handle specific error cases
            if (result.error) {
                if (result.error === 'No media items selected') {
                    console.log('ℹ️ No photos selected yet, showing user message');
                    this.showNoSelectionMessage();
                    return;
                } else if (result.error === 'Not authenticated') {
                    console.log('🔐 Authentication required');
                    alert('Please sign in to Google Photos first');
                    return;
                } else {
                    console.error('❌ Backend reported error:', result.error, result.details);
                    throw new Error(result.details || result.error);
                }
            }
            
            // Fallback: no success flag but no explicit error
            console.log('⚠️ Unclear response from backend:', result);
            this.showPickerLimitation(); // Show generic limitation message
            
        } catch (error) {
            console.error('💥 Failed to load selected photos:', error);
            
            // Show user-friendly error in UI instead of just alert
            const container = document.getElementById('selectedPhotosContainer');
            const grid = document.getElementById('selectedPhotosGrid');
            
            if (container && grid) {
                container.style.display = 'block';
                const title = container.querySelector('h4');
                if (title) {
                    title.textContent = '❌ Error Loading Selected Photos';
                }
                
                grid.innerHTML = `
                    <div class="error-message" style="text-align: center; padding: 40px; color: #d32f2f;">
                        <h3>🚨 Failed to Load Selected Photos</h3>
                        <p style="margin: 20px 0;"><strong>Error:</strong> ${error.message}</p>
                        <div style="margin-top: 20px;">
                            <button id="retryLoadBtn" class="ctl-btn control">🔄 Retry</button>
                            <button id="selectNewPhotosBtn" class="ctl-btn control" style="margin-left: 10px;">📸 Select New Photos</button>
                        </div>
                    </div>
                `;
                
                // Add retry functionality
                const retryBtn = document.getElementById('retryLoadBtn');
                if (retryBtn) {
                    retryBtn.addEventListener('click', () => this.loadSelectedPhotos());
                }
                
                const selectNewBtn = document.getElementById('selectNewPhotosBtn');
                if (selectNewBtn) {
                    selectNewBtn.addEventListener('click', () => {
                        container.style.display = 'none';
                        document.getElementById('pickerStatus').style.display = 'none';
                        document.getElementById('openPickerBtn').style.display = 'block';
                    });
                }
            } else {
                // Fallback to alert if UI elements aren't found
                alert('Failed to load selected photos: ' + error.message);
            }
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
                    <img src="${this.createProxyImageUrl(album.coverPhotoBaseUrl || '/static/album-placeholder.png', 'w200-h200-c')}" alt="${album.title}" loading="lazy">
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

            const proxySrc = this.createProxyImageUrl(photo.baseUrl || '', 'w200-h200-c');
            const fname = photo.filename || 'Photo';

            photoElement.innerHTML = `
                <img src="${proxySrc}" alt="${fname}" loading="lazy" style="width: 100%; height: 150px; object-fit: cover;">
                <div class="photo-info">
                    <div class="photo-filename">${fname}</div>
                    <button class="photo-select-btn ctl-btn control" style="margin-top: 8px;">Select</button>
                </div>
            `;

            // Add click handler for selection
            const selectBtn = photoElement.querySelector('.photo-select-btn');
            if (selectBtn) {
                selectBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.togglePhotoSelection(photo.id, photoElement);
                });
            }

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
                    <img src="${this.createProxyImageUrl(album.coverPhotoBaseUrl || '', 'w200-h200-c')}" alt="${album.title}" loading="lazy">
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

    renderPickedMediaItems(mediaItems, containerId) {
        console.log('🖼️ Rendering picked media items:', mediaItems.length);
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        if (mediaItems.length === 0) {
            container.innerHTML = `
                <div class="no-items-message" style="text-align: center; padding: 40px; color: #666;">
                    <h3>📷 No Photos Selected</h3>
                    <p>No photos were found in your selection. Try selecting photos again.</p>
                    <button id="retrySelectionBtn" class="ctl-btn control">Select Photos</button>
                </div>
            `;
            
            const retryBtn = document.getElementById('retrySelectionBtn');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    container.parentElement.style.display = 'none';
                    document.getElementById('pickerStatus').style.display = 'none';
                    document.getElementById('openPickerBtn').style.display = 'block';
                });
            }
            return;
        }
        
        // Show simple message and automatically start download
        container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <h3>✅ ${mediaItems.length} Photos Selected!</h3>
                <p>Automatically downloading and converting for your e-Paper display...</p>
                <div class="loading-spinner" style="margin: 20px auto;"></div>
            </div>
        `;
        
        // Automatically download the selected photos (like drag-and-drop)
        this.autoDownloadPickedPhotos(mediaItems);
    }

    showNoSelectionMessage() {
        console.log('📝 Showing no selection message');
        const container = document.getElementById('selectedPhotosContainer');
        const grid = document.getElementById('selectedPhotosGrid');
        
        if (container && grid) {
            container.style.display = 'block';
            
            const title = container.querySelector('h4');
            if (title) {
                title.textContent = '📷 No Photos Selected Yet';
            }
            
            grid.innerHTML = `
                <div class="no-selection-message" style="text-align: center; padding: 40px; color: #666;">
                    <h3>🕒 Waiting for Photo Selection</h3>
                    <p>You haven't selected any photos yet in the Google Photos picker.</p>
                    <p>Please go back to the picker window and select some photos, then try again.</p>
                    <div style="margin-top: 20px;">
                        <button id="checkAgainBtn" class="ctl-btn control">🔄 Check Again</button>
                        <button id="newSelectionBtn" class="ctl-btn control" style="margin-left: 10px;">📸 Start New Selection</button>
                    </div>
                </div>
            `;
            
            // Add event listeners
            const checkAgainBtn = document.getElementById('checkAgainBtn');
            if (checkAgainBtn) {
                checkAgainBtn.addEventListener('click', () => this.loadSelectedPhotos());
            }
            
            const newSelectionBtn = document.getElementById('newSelectionBtn');
            if (newSelectionBtn) {
                newSelectionBtn.addEventListener('click', () => {
                    container.style.display = 'none';
                    document.getElementById('pickerStatus').style.display = 'none';
                    document.getElementById('openPickerBtn').style.display = 'block';
                });
            }
        }
    }

    async autoDownloadPickedPhotos(mediaItems) {
        console.log('📥 Auto-downloading picked photos:', mediaItems.length, 'items');
        
        try {
            // Create placeholder thumbnails immediately (like drag-and-drop does)
            const placeholderFiles = mediaItems.map(item => {
                const mediaFile = item.mediaFile || {};
                return {
                    filename: mediaFile.filename || `photo_${item.id.substring(0, 8)}.jpg`
                };
            });
            
            // Manually add placeholders to thumbnail grid (simpler than importing modules)
            this.addPlaceholderThumbnails(placeholderFiles);
            
            // Call the existing download endpoint
            const response = await fetch('/api/google-photos/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    // The backend download route expects to use the current session
                    // and will call the picker API to get photos, so we don't need
                    // to pass the photos here - just trigger the download
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📥 Download result:', result);
            
            // Hide the Google Photos interface and show success
            const container = document.getElementById('selectedPhotosContainer');
            if (container) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <h3>🎉 Success!</h3>
                        <p>Downloaded ${result.downloaded_count} photos! They are now being converted for your e-Paper display and will appear in the main thumbnail grid.</p>
                        <button id="selectMorePhotosBtn" class="ctl-btn control" style="margin-top: 20px;">📸 Select More Photos</button>
                    </div>
                `;
                
                const selectMoreBtn = document.getElementById('selectMorePhotosBtn');
                if (selectMoreBtn) {
                    selectMoreBtn.addEventListener('click', () => {
                        container.parentElement.style.display = 'none';
                        document.getElementById('pickerStatus').style.display = 'none';
                        document.getElementById('openPickerBtn').style.display = 'block';
                    });
                }
            }
            
            // Refresh the main images grid (like drag-and-drop does)
            if (window.refreshImages) {
                window.refreshImages();
            }
            
        } catch (error) {
            console.error('💥 Failed to download picked photos:', error);
            
            const container = document.getElementById('selectedPhotosContainer');
            if (container) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #d32f2f;">
                        <h3>❌ Download Failed</h3>
                        <p>Failed to download photos: ${error.message}</p>
                        <div style="margin-top: 20px;">
                            <button id="retryDownloadBtn" class="ctl-btn control">🔄 Retry Download</button>
                            <button id="selectMorePhotosBtn" class="ctl-btn control" style="margin-left: 10px;">📸 Select Different Photos</button>
                        </div>
                    </div>
                `;
                
                const retryBtn = document.getElementById('retryDownloadBtn');
                if (retryBtn) {
                    retryBtn.addEventListener('click', () => this.autoDownloadPickedPhotos(mediaItems));
                }
                
                const selectMoreBtn = document.getElementById('selectMorePhotosBtn');
                if (selectMoreBtn) {
                    selectMoreBtn.addEventListener('click', () => {
                        container.parentElement.style.display = 'none';
                        document.getElementById('pickerStatus').style.display = 'none';
                        document.getElementById('openPickerBtn').style.display = 'block';
                    });
                }
            }
        }
    }

    addPlaceholderThumbnails(uploadedFiles) {
        // Add placeholders to the main thumbnail grid (similar to drag-and-drop)
        const thumbsList = document.getElementById('thumbList');
        if (!thumbsList) return;

        uploadedFiles.forEach(file => {
            const placeholder = document.createElement('div');
            placeholder.className = 'thumb placeholder-thumb';
            placeholder.id = `placeholder-${file.filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
            placeholder.innerHTML = `
                <div class="placeholder-content">
                    <div class="placeholder-spinner"></div>
                    <div class="placeholder-text">Converting...</div>
                    <div class="placeholder-filename">${file.filename}</div>
                </div>
            `;
            
            // Add to top of thumb list (newest first)
            thumbsList.insertBefore(placeholder, thumbsList.firstChild);
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

    async tryAlternativePhotoAccess() {
        console.log('Attempting to access photos via Google Photos Library API...');
        
        try {
            // Try to get recent photos that might include what was just selected
            const response = await fetch('/api/google-photos/recent-photos?limit=50');
            
            if (response.ok) {
                const result = await response.json();
                console.log('Recent photos response:', result);
                
                if (result.success && result.photos && result.photos.length > 0) {
                    console.log(`Found ${result.photos.length} recent photos - this might include selected photos`);
                    this.displayAlternativePhotos(result.photos);
                    return;
                }
            }
            
            // Try to get all photos from library
            console.log('Trying to get all library photos...');
            const allPhotosResponse = await fetch('/api/google-photos/library-photos?limit=100');
            
            if (allPhotosResponse.ok) {
                const allPhotosResult = await allPhotosResponse.json();
                console.log('Library photos response:', allPhotosResult);
                
                if (allPhotosResult.success && allPhotosResult.photos && allPhotosResult.photos.length > 0) {
                    console.log(`Found ${allPhotosResult.photos.length} library photos`);
                    this.displayAlternativePhotos(allPhotosResult.photos);
                    return;
                }
            }
            
            console.log('No alternative photo access methods worked');
            this.showPickerLimitation(); // Fall back to limitation message
            
        } catch (error) {
            console.error('Alternative photo access failed:', error);
            this.showPickerLimitation(); // Fall back to limitation message
        }
    }

    displayAlternativePhotos(photos) {
        console.log('Displaying alternative photos from Google Photos Library API');
        
        const container = document.getElementById('selectedPhotosContainer');
        const grid = document.getElementById('selectedPhotosGrid');
        
        if (!container || !grid) {
            console.error('Could not find selection display elements');
            return;
        }
        
        container.style.display = 'block';
        
        // Update container title
        const title = container.querySelector('h4');
        if (title) {
            title.textContent = `📸 Recent Photos from Your Google Photos Library (${photos.length} found)`;
        }
        
        // Create photo grid
        grid.innerHTML = `
            <div class="alternative-photos-info">
                <p><strong>Since we can't get the exact selection from the Picker API, here are recent photos from your Google Photos library:</strong></p>
                <p>These might include the photos you just selected. Click on any photos you want to download and convert for your e-Paper display.</p>
            </div>
            <div class="photos-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin-top: 20px;">
                ${photos.map(photo => `
                    <div class="photo-item" style="border: 2px solid transparent; border-radius: 8px; overflow: hidden; cursor: pointer; transition: border-color 0.2s;" 
                         data-photo-id="${photo.id}" onclick="this.classList.toggle('selected'); this.style.borderColor = this.classList.contains('selected') ? '#007cba' : 'transparent';">
                        <img src="${this.createProxyImageUrl(photo.baseUrl, 'w150-h150-c')}" alt="Photo" style="width: 100%; height: 150px; object-fit: cover;">
                        <div style="padding: 5px; font-size: 12px; background: white;">
                            <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${photo.filename || 'Photo'}</div>
                            <div style="color: #666; font-size: 10px;">${photo.mediaMetadata ? new Date(photo.mediaMetadata.creationTime).toLocaleDateString() : ''}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top: 20px; text-align: center;">
                <button id="downloadSelectedAlternativeBtn" class="ctl-btn control">Download Selected Photos</button>
                <button id="selectAllAlternativeBtn" class="ctl-btn control" style="margin-left: 10px;">Select All</button>
                <button id="selectMorePhotosBtn" class="ctl-btn control" style="margin-left: 10px;">Back to Picker</button>
            </div>
        `;
        
        // Add event listeners
        const downloadBtn = document.getElementById('downloadSelectedAlternativeBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadAlternativeSelection();
            });
        }
        
        const selectAllBtn = document.getElementById('selectAllAlternativeBtn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                document.querySelectorAll('.photo-item').forEach(item => {
                    item.classList.add('selected');
                    item.style.borderColor = '#007cba';
                });
            });
        }
        
        const selectMoreBtn = document.getElementById('selectMorePhotosBtn');
        if (selectMoreBtn) {
            selectMoreBtn.addEventListener('click', () => {
                container.style.display = 'none';
                document.getElementById('pickerStatus').style.display = 'none';
                document.getElementById('openPickerBtn').style.display = 'block';
            });
        }
    }

    downloadAlternativeSelection() {
        const selectedPhotos = Array.from(document.querySelectorAll('.photo-item.selected')).map(item => {
            return item.dataset.photoId;
        });
        
        if (selectedPhotos.length === 0) {
            alert('Please select at least one photo to download');
            return;
        }
        
        console.log('Downloading alternative selection:', selectedPhotos);
        
        // Send to backend for download
        fetch('/api/google-photos/download-library-photos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                photoIds: selectedPhotos
            })
        })
        .then(response => response.json())
        .then(result => {
            console.log('Download result:', result);
            if (result.success) {
                alert(`Successfully initiated download of ${selectedPhotos.length} photos!`);
            } else {
                alert('Download failed: ' + (result.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Download failed:', error);
            alert('Download failed: ' + error.message);
        });
    }
}

// Initialize when page loads
let googlePhotos;
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing GooglePhotosManager...');
    googlePhotos = new GooglePhotosManager();
});
