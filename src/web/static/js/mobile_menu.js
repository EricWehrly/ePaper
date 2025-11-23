/* Mobile Hamburger Menu */

console.log('Mobile menu: Starting');

function initMobileMenu() {
    const hamburgerBtn = document.querySelector('.hamburger-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (!hamburgerBtn || !mobileMenu) {
        console.log('Mobile menu: Elements not found (probably desktop view)');
        return;
    }
    
    // Toggle menu on hamburger click
    hamburgerBtn.addEventListener('click', () => {
        mobileMenu.classList.toggle('open');
    });
    
    // Close menu when clicking a link
    const menuLinks = mobileMenu.querySelectorAll('a');
    menuLinks.forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.remove('open');
        });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!hamburgerBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
            mobileMenu.classList.remove('open');
        }
    });
    
    console.log('Mobile menu: Initialized');
}

// Run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileMenu);
} else {
    initMobileMenu();
}

console.log('Mobile menu: Script loaded');
