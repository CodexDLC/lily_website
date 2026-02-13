// 1. Mobile Menu Toggle
function toggleMenu() {
    const menu = document.getElementById('mobileMenu');
    if(menu) {
        menu.classList.toggle('active');
        document.body.classList.toggle('no-scroll');
    }
}

// 2. Footer Toggle
function toggleFooter() {
    const footer = document.querySelector('.footer-smart');
    const btn = document.getElementById('footerToggleBtn');
    const btnText = document.getElementById('footerBtnText');

    if(footer && btn && btnText) {
        footer.classList.toggle('active');
        if (footer.classList.contains('active')) {
            btnText.innerText = btn.dataset.textClose;
        } else {
            btnText.innerText = btn.dataset.textOpen;
        }
    }
}
