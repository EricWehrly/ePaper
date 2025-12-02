/* Simple Tab Switcher - Handles tab clicks and URL query parameters */

console.log('Tab switcher: Starting');

/**
 * Switch to a specific tab
 * @param {string} tabName - The tab to switch to (library, playlists, photos)
 */
function switchToTab(tabName) {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    // Update active button
    tabButtons.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Show/hide panes
    tabPanes.forEach(pane => {
        if (pane.dataset.pane === tabName) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });
}

/**
 * Check URL for ?tab= parameter and switch to that tab
 */
function checkTabParameter() {
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    
    if (tabParam) {
        const validTabs = ['library', 'playlists', 'photos'];
        if (validTabs.includes(tabParam)) {
            console.log(`Tab switcher: Switching to tab from URL parameter: ${tabParam}`);
            switchToTab(tabParam);
        }
    }
}

function initTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    if (tabButtons.length === 0) {
        console.warn('Tab switcher: No tab buttons found');
        return;
    }
    
    console.log(`Tab switcher: Found ${tabButtons.length} tabs`);
    
    tabButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const targetTab = e.currentTarget.dataset.tab;
            switchToTab(targetTab);
        });
    });
    
    // Check for tab parameter in URL
    checkTabParameter();
    
    console.log('Tab switcher: Initialized');
}

// Run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTabSwitching);
} else {
    initTabSwitching();
}

console.log('Tab switcher: Script loaded');
