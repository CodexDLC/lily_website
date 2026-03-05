/**
 * PWA Functionality for LILY Website
 * Handles Service Worker registration and installation prompt
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Service Worker Registration
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js', {
                scope: '/'
            })
            .then(registration => {
                console.log('✅ Service Worker registered:', registration.scope);

                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('🔄 Service Worker update found...');

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            console.log('✨ New version available');
                            // Optional: Show update notification to user
                        }
                    });
                });
            })
            .catch(err => {
                console.error('❌ Service Worker registration failed:', err);
            });
        });

        // Handle messages from Service Worker
        navigator.serviceWorker.addEventListener('message', event => {
            if (event.data && event.data.type === 'CACHE_CLEARED') {
                console.log('🗑️ Cache cleared');
            }
        });
    }

    // 2. PWA Install Prompt Logic
    let deferredPrompt;
    let installBannerShown = false;

    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent Chrome 67 and earlier from automatically showing the prompt
        e.preventDefault();
        // Stash the event so it can be triggered later.
        deferredPrompt = e;

        // Check if user has dismissed the prompt recently (within 7 days)
        if (shouldShowInstallBanner()) {
            // Show the banner after a delay to not be intrusive
            setTimeout(() => {
                showInstallBanner();
            }, 5000);
        }
    });

    function shouldShowInstallBanner() {
        try {
            const dismissed = localStorage.getItem('pwa-install-dismissed');
            if (dismissed) {
                const daysSinceDismissed = (Date.now() - parseInt(dismissed)) / (1000 * 60 * 60 * 24);
                if (daysSinceDismissed < 7) {
                    return false;
                }
            }
            return true;
        } catch (e) {
            console.error('localStorage unavailable', e);
            return true; // Default to showing if storage fails
        }
    }

    function showInstallBanner() {
        if (installBannerShown || !deferredPrompt) {
            return;
        }

        installBannerShown = true;

        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';

        // Content
        banner.innerHTML = `
            <span style="font-size: 20px;">📱</span>
            <span style="flex: 1;">Установите приложение LILY</span>
            <button id="pwa-install-btn">Установить</button>
            <button id="pwa-dismiss-btn">✕</button>
        `;

        document.body.appendChild(banner);

        // Event Listeners
        const installBtn = document.getElementById('pwa-install-btn');
        const dismissBtn = document.getElementById('pwa-dismiss-btn');

        if (installBtn) {
            installBtn.addEventListener('click', installPWA);
        }
        if (dismissBtn) {
            dismissBtn.addEventListener('click', dismissInstallBanner);
        }
    }

    async function installPWA() {
        if (!deferredPrompt) {
            return;
        }
        // Show the install prompt
        deferredPrompt.prompt();
        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`Install outcome: ${outcome}`);

        // We've used the prompt, and can't use it again, throw it away
        deferredPrompt = null;

        // Hide the banner
        dismissInstallBanner();
    }

    function dismissInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.style.animation = 'slideDown 0.3s ease forwards';
            setTimeout(() => banner.remove(), 300);
        }

        // Save dismissal timestamp
        try {
            localStorage.setItem('pwa-install-dismissed', Date.now().toString());
        } catch (e) {}
    }

    window.addEventListener('appinstalled', () => {
        console.log('✅ PWA successfully installed');
        deferredPrompt = null;
    });
});
