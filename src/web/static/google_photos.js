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
            console.log('Disconnecting...');
            window.location.href = '/api/google-photos/disconnect';
        } else {
            console.log('Connecting...');
            window.location.href = '/api/google-photos/auth';
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
