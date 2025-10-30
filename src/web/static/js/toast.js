/**
 * Simple Toast Notification System
 */

class Toast {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in ms (0 = persistent)
     * @param {string} title - Optional title
     */
    show(message, type = 'info', duration = 5000, title = null) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}${duration === 0 ? ' persistent' : ''}`;

        const content = document.createElement('div');
        content.className = 'toast-content';

        if (title) {
            const titleEl = document.createElement('div');
            titleEl.className = 'toast-title';
            titleEl.textContent = title;
            content.appendChild(titleEl);
        }

        const messageEl = document.createElement('div');
        messageEl.className = 'toast-message';
        messageEl.textContent = message;
        content.appendChild(messageEl);

        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '×';
        closeBtn.addEventListener('click', () => this.remove(toast));

        toast.appendChild(content);
        toast.appendChild(closeBtn);

        this.container.appendChild(toast);

        // Auto-dismiss if duration > 0
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }

        return toast;
    }

    remove(toast) {
        if (toast && toast.parentNode) {
            toast.style.animation = 'toast-slide-out 0.3s ease-in';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }

    // Convenience methods
    success(message, duration = 5000, title = null) {
        return this.show(message, 'success', duration, title);
    }

    error(message, duration = 0, title = 'Error') {
        return this.show(message, 'error', duration, title);
    }

    warning(message, duration = 8000, title = 'Warning') {
        return this.show(message, 'warning', duration, title);
    }

    info(message, duration = 5000, title = null) {
        return this.show(message, 'info', duration, title);
    }
}

// Create global toast instance
const toast = new Toast();

// Export for modules and make available globally
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Toast, toast };
} else {
    window.toast = toast;
}