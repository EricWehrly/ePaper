/* Simple Tab Switcher - Just handles tab clicks, no DOM manipulation */

console.log('Tab switcher: Starting');

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
            
            // Update active button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            e.currentTarget.classList.add('active');
            
            // Show/hide panes
            tabPanes.forEach(pane => {
                if (pane.dataset.pane === targetTab) {
                    pane.classList.add('active');
                } else {
                    pane.classList.remove('active');
                }
            });
        });
    });
    
    console.log('Tab switcher: Initialized');
}

// Run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTabSwitching);
} else {
    initTabSwitching();
}

console.log('Tab switcher: Script loaded');
