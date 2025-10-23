/**
 * Ngrok Redirect Banner Implementation
 * 
 * Handles the countdown banner that redirects users from raspberrypi.local
 * to the ngrok HTTPS URL for OAuth authentication.
 */

class NgrokBanner {
    constructor() {
        this.banner = null;
        this.countdownElement = null;
        this.countdownInterval = null;
        this.settings = null;
        this.ngrokInfo = null;
        this.sessionKey = 'ngrok_banner_dismissed';
    }

    /**
     * Initialize and check if banner should be shown
     */
    async init() {
        try {
            // Only proceed if we're on raspberrypi.local
            if (!this.isRaspberryPiLocal()) {
                return;
            }

            // Check if user dismissed banner in this session
            if (this.wasDismissedThisSession()) {
                return;
            }

            // Fetch configuration and ngrok info
            await this.loadConfiguration();

            // Check if banner should be shown
            if (this.shouldShowBanner()) {
                this.showBanner();
            }
        } catch (error) {
            console.error('NgrokBanner initialization failed:', error);
        }
    }

    /**
     * Check if current domain is raspberrypi.local
     */
    isRaspberryPiLocal() {
        return window.location.hostname === 'raspberrypi.local';
    }

    /**
     * Check if banner was dismissed in this session
     */
    wasDismissedThisSession() {
        return sessionStorage.getItem(this.sessionKey) === 'true';
    }

    /**
     * Load settings and ngrok info from API
     */
    async loadConfiguration() {
        // Load settings
        const settingsResponse = await fetch('/api/settings');
        if (!settingsResponse.ok) {
            throw new Error('Failed to load settings');
        }
        this.settings = await settingsResponse.json();

        // Load ngrok info
        const ngrokResponse = await fetch('/api/ngrok-info');
        if (!ngrokResponse.ok) {
            throw new Error('Failed to load ngrok info');
        }
        this.ngrokInfo = await ngrokResponse.json();
    }

    /**
     * Determine if banner should be shown based on configuration
     */
    shouldShowBanner() {
        // Check if feature is enabled
        if (!this.settings?.ngrok_redirect?.enabled) {
            return false;
        }

        // Check if ngrok is available and has HTTPS tunnel
        if (!this.ngrokInfo?.ngrok_available || !this.ngrokInfo?.tunnel_active) {
            return false;
        }

        // Check if user is already authenticated (optional check)
        // For now, we'll always show if conditions are met
        return true;
    }

    /**
     * Show the banner with countdown
     */
    showBanner() {
        this.banner = document.getElementById('ngrokBanner');
        this.countdownElement = document.getElementById('bannerCountdown');
        
        if (!this.banner || !this.countdownElement) {
            console.error('Banner elements not found in DOM');
            return;
        }

        // Show banner
        this.banner.style.display = 'block';
        document.body.classList.add('banner-active');

        // Setup event listeners
        this.setupEventListeners();

        // Start countdown
        this.startCountdown();
    }

    /**
     * Setup banner button event listeners
     */
    setupEventListeners() {
        const redirectNowBtn = document.getElementById('redirectNowBtn');
        const cancelRedirectBtn = document.getElementById('cancelRedirectBtn');

        if (redirectNowBtn) {
            redirectNowBtn.addEventListener('click', () => {
                this.redirectToNgrok();
            });
        }

        if (cancelRedirectBtn) {
            cancelRedirectBtn.addEventListener('click', () => {
                this.dismissBanner();
            });
        }
    }

    /**
     * Start the countdown timer
     */
    startCountdown() {
        let secondsLeft = this.settings.ngrok_redirect.countdown_seconds;
        this.countdownElement.textContent = secondsLeft;

        this.countdownInterval = setInterval(() => {
            secondsLeft--;
            this.countdownElement.textContent = secondsLeft;

            if (secondsLeft <= 0) {
                this.redirectToNgrok();
            }
        }, 1000);
    }

    /**
     * Redirect to the ngrok HTTPS URL
     */
    redirectToNgrok() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }

        if (this.ngrokInfo?.public_url) {
            // Preserve the current path and query parameters
            const currentPath = window.location.pathname + window.location.search;
            const ngrokUrl = this.ngrokInfo.public_url + currentPath;
            window.location.href = ngrokUrl;
        } else {
            console.error('No ngrok public URL available');
            this.dismissBanner();
        }
    }

    /**
     * Dismiss the banner and remember the choice for this session
     */
    dismissBanner() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }

        if (this.banner) {
            this.banner.style.display = 'none';
            document.body.classList.remove('banner-active');
        }

        // Remember dismissal for this session
        sessionStorage.setItem(this.sessionKey, 'true');
    }
}

// Initialize banner when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const banner = new NgrokBanner();
        banner.init();
    });
} else {
    const banner = new NgrokBanner();
    banner.init();
}