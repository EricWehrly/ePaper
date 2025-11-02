/* ePaper Display Toggle - Show/Hide display area functionality */

export class DisplayToggle {
    constructor() {
        this.displayContainer = null;
        this.toggleButton = null;
        this.isCollapsed = false;
        this.isMobile = window.innerWidth < 768;
        
        this.init();
        this.setupEventListeners();
    }

    init() {
        // Find the display box (not the entire section)
        const displayBox = document.querySelector('.display-box');
        if (!displayBox) return;

        // Wrap only the display-box in collapsible container
        if (!displayBox.parentNode.classList.contains('display-container')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'display-container';
            displayBox.parentNode.insertBefore(wrapper, displayBox);
            wrapper.appendChild(displayBox);
            this.displayContainer = wrapper;
        } else {
            this.displayContainer = displayBox.parentNode;
        }

        // Create toggle button
        this.createToggleButton();
        
        // Set initial state based on screen size
        this.updateToggleState();
    }

    createToggleButton() {
        // Desktop toggle button (top-right corner)
        const desktopToggle = document.createElement('button');
        desktopToggle.className = 'display-toggle desktop-only';
        desktopToggle.innerHTML = '−'; // Minimize symbol
        desktopToggle.setAttribute('aria-label', 'Toggle display area');
        desktopToggle.setAttribute('data-tooltip', 'Hide display area');
        
        // Mobile toggle button (full width)
        const mobileToggle = document.createElement('button');
        mobileToggle.className = 'mobile-display-toggle mobile-only';
        mobileToggle.innerHTML = '<span class="toggle-text">Show/Hide Display</span>';
        mobileToggle.setAttribute('aria-label', 'Toggle display area');

        // Add desktop button to display container
        this.displayContainer.appendChild(desktopToggle);
        
        // Add mobile button before the display section (not just the display container)
        const displaySection = document.querySelector('.display-section');
        if (displaySection) {
            displaySection.parentNode.insertBefore(mobileToggle, displaySection);
        }

        // Store references
        this.desktopToggle = desktopToggle;
        this.mobileToggle = mobileToggle;

        // Add click handlers
        desktopToggle.addEventListener('click', () => this.toggle());
        mobileToggle.addEventListener('click', () => this.toggle());
    }

    setupEventListeners() {
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
        if (!this.displayContainer) return;

        this.isCollapsed = true;
        
        if (animate) {
            this.displayContainer.style.transition = 'var(--transition-medium)';
        } else {
            this.displayContainer.style.transition = 'none';
        }

        if (this.isMobile) {
            this.displayContainer.classList.add('mobile-collapsed');
        } else {
            this.displayContainer.classList.add('collapsed');
        }

        this.updateToggleButtons();
        
        // Reset transition after animation
        if (animate) {
            setTimeout(() => {
                if (this.displayContainer) {
                    this.displayContainer.style.transition = '';
                }
            }, 300);
        }

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('displayToggle', { 
            detail: { collapsed: true, isMobile: this.isMobile }
        }));
    }

    expand(animate = true) {
        if (!this.displayContainer) return;

        this.isCollapsed = false;
        
        if (animate) {
            this.displayContainer.style.transition = 'var(--transition-medium)';
        } else {
            this.displayContainer.style.transition = 'none';
        }

        this.displayContainer.classList.remove('collapsed', 'mobile-collapsed');
        this.updateToggleButtons();

        // Reset transition after animation
        if (animate) {
            setTimeout(() => {
                if (this.displayContainer) {
                    this.displayContainer.style.transition = '';
                }
            }, 300);
        }

        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('displayToggle', { 
            detail: { collapsed: false, isMobile: this.isMobile }
        }));
    }

    updateToggleButtons() {
        if (this.desktopToggle) {
            this.desktopToggle.innerHTML = this.isCollapsed ? '+' : '−';
            this.desktopToggle.setAttribute('data-tooltip', 
                this.isCollapsed ? 'Show display area' : 'Hide display area'
            );
        }

        if (this.mobileToggle) {
            const toggleText = this.mobileToggle.querySelector('.toggle-text');
            if (toggleText) {
                toggleText.textContent = this.isCollapsed ? 'Show Display' : 'Hide Display';
            }
        }
    }

    updateToggleState() {
        // Update mobile state
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth < 768;

        // If switching between mobile/desktop, update classes
        if (wasMobile !== this.isMobile && this.isCollapsed) {
            this.displayContainer.classList.remove('collapsed', 'mobile-collapsed');
            if (this.isMobile) {
                this.displayContainer.classList.add('mobile-collapsed');
            } else {
                this.displayContainer.classList.add('collapsed');
            }
        }

        this.updateToggleButtons();
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