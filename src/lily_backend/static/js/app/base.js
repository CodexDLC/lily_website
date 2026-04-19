document.addEventListener('DOMContentLoaded', function() {
    initMobileMenu();
    initFooter();
});

// 1. Mobile Menu
function initMobileMenu() {
    const burgerBtn = document.querySelector('.burger-btn');
    const closeBtn = document.querySelector('.close-btn');
    const menu = document.getElementById('mobileMenu');
    const navLinks = document.querySelectorAll('.mobile-nav-links a');

    function toggleMenu() {
        if(menu) {
            menu.classList.toggle('active');
            document.body.classList.toggle('no-scroll');
        }
    }

    if(burgerBtn) burgerBtn.addEventListener('click', toggleMenu);
    if(closeBtn) closeBtn.addEventListener('click', toggleMenu);

    // Close menu when clicking a link
    navLinks.forEach(link => {
        link.addEventListener('click', toggleMenu);
    });
}

// 2. Footer Toggle
function initFooter() {
    const footer = document.querySelector('.footer-smart');
    const footerBar = document.getElementById('footerBar');
    const footerCredits = document.getElementById('footerCredits');
    const footerControls = document.getElementById('footerControls');
    const toggleBtn = document.getElementById('footerToggleBtn');

    function toggleFooter() {
        if(footer) {
            footer.classList.toggle('active');
        }
    }

    // Toggle on bar click (background area)
    if(footerBar) {
        footerBar.addEventListener('click', toggleFooter);
    }

    // Toggle on button click (Explicitly needed because parent stops propagation)
    if(toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            toggleFooter();
            // We don't need stopPropagation here because the parent footerControls already stops it,
            // or if it bubbles, it hits footerBar which toggles it again (double toggle).
            // So we MUST stop propagation here to prevent double toggle if logic changes,
            // OR just rely on the fact that footerControls stops it.
            // Given footerControls stops it, this is safe.
        });
    }

    // Stop propagation for interactive elements inside the bar
    // This prevents clicking on "Developed by" or "Language Switcher" from toggling the footer
    if(footerCredits) {
        footerCredits.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    if(footerControls) {
        footerControls.addEventListener('click', function(e) {
            // Only stop propagation if the click is NOT on the toggle button
            // But since toggleBtn has its own listener now, we can just stop everything else.
            // However, if we click the button, this fires first (bubbling) or second?
            // Actually, button is inside controls. Button click -> Button Handler -> Controls Handler.

            // If we stop propagation here, it won't reach footerBar. That's Good.
            e.stopPropagation();
        });
    }
}

// 3. HTMX CSRF Configuration
document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 4. Auth Modal
function openAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.classList.add('active');
        document.body.classList.add('no-scroll');
    }
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.classList.remove('no-scroll');
    }
}

// Close modal when clicking outside the card
document.addEventListener('click', function(e) {
    const modal = document.getElementById('authModal');
    if (modal && e.target === modal) {
        closeAuthModal();
    }
});

// ESC key to close
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('authModal');
        if (modal && modal.classList.contains('active')) {
            closeAuthModal();
        }
    }
});
