/* ePaper Display Toggle - Show/Hide display area functionality */

export class DisplayToggle {
    constructor() {
        this.displayContent = null;
        this.toggleButton = null;
        this.isCollapsed = false;
        this.isMobile = window.innerWidth < 768;
        
        // Wait for main tabs to initialize first
        setTimeout(() => this.init(), 200);
    }

    init() {
        // Find the display content area (what we actually hide/show)
        this.displayContent = document.querySelector('.display-content, #displayContent');
        if (!this.displayContent) {
            console.warn('Display content not found, retrying...');
            setTimeout(() => this.init(), 100);
            return;
        }

        // Find the existing toggle button from template
        this.toggleButton = document.querySelector('#displayToggleBtn, .display-toggle-btn');
        if (!this.toggleButton) {
            console.warn('Display toggle button not found, creating fallback');
            this.createToggleButton();
        }

        this.setupEventListeners();
        this.updateToggleState();
        
        // Restore saved state
        const savedState = localStorage.getItem('epaper_display_collapsed');
        if (savedState === 'true') {
            this.collapse(false); // Don't animate on initial load
        }
        
        console.log('Display toggle initialized:', {
            displayContent: !!this.displayContent,
            toggleButton: !!this.toggleButton,
            isCollapsed: this.isCollapsed
        });
    }

    createToggleButton() {
        const displayHeader = document.querySelector('.display-header, .display-section');
        if (displayHeader) {
            const button = document.createElement('button');
            button.id = 'displayToggleBtn';
            button.className = 'display-toggle-btn';
            button.setAttribute('aria-label', 'Toggle display visibility');
            button.innerHTML = `
                <span class="toggle-icon">👁️</span>
                <span class="toggle-text">Hide</span>
            `;
            displayHeader.appendChild(button);
            this.toggleButton = button;
        }
    }

    setupEventListeners() {
        // Main toggle button (from template)
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', () => this.toggle());
        }
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.isMobile = window.innerWidth < 768;
                this.updateToggleState();
            }, 150);
        });

        // Handle keyboard shortcuts (desktop only)
        document.addEventListener('keydown', (e) => {
            if (!this.isMobile && e.key === 'd' && e.ctrlKey && !e.shiftKey) {
                e.preventDefault();
                this.toggle();
            }
        });

        // Save state to localStorage
        window.addEventListener('beforeunload', () => {
            localStorage.setItem('epaper_display_collapsed', this.isCollapsed.toString());
        });

        // Restore state from localStorage
        const savedState = localStorage.getItem('epaper_display_collapsed');
        if (savedState === 'true') {
            this.collapse(false); // Don't animate on initial load
        }
    }

    toggle() {
        if (this.isCollapsed) {
            this.expand();
        } else {
            this.collapse();
        }
    }

    collapse(animate = true) {
        if (!this.displayContent) return;

        this.isCollapsed = true;
        
        if (animate) {
            this.displayContent.style.transition = 'height var(--transition-medium), opacity var(--transition-medium)';
        } else {
            this.displayContent.style.transition = 'none';
        }

        // Hide the display content
        this.displayContent.style.height = '0';
        this.displayContent.style.opacity = '0';
        this.displayContent.style.overflow = 'hidden';

        this.updateToggleButton();
        
        // Reset transition after animation
        if (animate) {
            setTimeout(() => {
                if (this.displayContent) {
                    this.displayContent.style.transition = '';
                }
            }, 300);
        }

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('displayToggle', { 
            detail: { collapsed: true, isMobile: this.isMobile }
        }));
    }

    expand(animate = true) {
        if (!this.displayContent) return;

        this.isCollapsed = false;
        
        if (animate) {
            this.displayContent.style.transition = 'height var(--transition-medium), opacity var(--transition-medium)';
        } else {
            this.displayContent.style.transition = 'none';
        }

        // Show the display content
        this.displayContent.style.height = 'auto';
        this.displayContent.style.opacity = '1';
        this.displayContent.style.overflow = 'visible';

        this.updateToggleButton();

        // Reset transition after animation
        if (animate) {
            setTimeout(() => {
                if (this.displayContent) {
                    this.displayContent.style.transition = '';
                }
            }, 300);
        }

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('displayToggle', { 
            detail: { collapsed: false, isMobile: this.isMobile }
        }));
    }

    updateToggleButton() {
        if (this.toggleButton) {
            const toggleText = this.toggleButton.querySelector('.toggle-text');
            const toggleIcon = this.toggleButton.querySelector('.toggle-icon');
            
            if (toggleText) {
                toggleText.textContent = this.isCollapsed ? 'Show' : 'Hide';
            }
            
            if (toggleIcon) {
                toggleIcon.textContent = this.isCollapsed ? '👁️' : '👁️‍🗨️';
            }
            
            this.toggleButton.setAttribute('aria-label', 
                this.isCollapsed ? 'Show display area' : 'Hide display area'
            );
        }
    }

    updateToggleState() {
        this.isMobile = window.innerWidth < 768;
        this.updateToggleButton();
    }

    // Public API
    getState() {
        return {
            isCollapsed: this.isCollapsed,
            isMobile: this.isMobile
        };
    }

    setState(collapsed, animate = true) {
        if (collapsed && !this.isCollapsed) {
            this.collapse(animate);
        } else if (!collapsed && this.isCollapsed) {
            this.expand(animate);
        }
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.displayToggle = new DisplayToggle();
    });
} else {
    window.displayToggle = new DisplayToggle();
}