/**
 * Promo Notification Widget
 *
 * Displays floating button with promotional offers and shows modal on click.
 * Uses localStorage to track viewed notifications and avoid showing them again.
 */

class PromoNotificationWidget {
    constructor() {
        this.notification = null;
        this.button = null;
        this.modal = null;
        this.API_BASE = '/api/v1/promos';
        this.STORAGE_KEY = 'lily_promo_seen_notifications';
    }

    /**
     * Initialize the widget with a delay to improve initial page load performance
     */
    async init() {
        try {
            // Get current page slug from URL
            const pageSlug = this.getCurrentPageSlug();

            // Fetch active notification from API
            const data = await this.fetchActiveNotification(pageSlug);

            if (!data) {
                return; // No active notifications
            }

            // Check if user already saw/closed this notification
            if (this.wasAlreadySeen(data.id)) {
                return;
            }

            this.notification = data;

            // Show floating button after the specified delay from DB
            // We already waited for window.load + 3s, so this is an additional delay if set
            setTimeout(() => {
                this.showFloatingButton();
                this.trackView();
            }, (data.display_delay || 0) * 1000);

        } catch (error) {
            console.error('[PromoNotification] Initialization error:', error);
        }
    }

    /**
     * Get current page slug from URL path
     */
    getCurrentPageSlug() {
        const path = window.location.pathname;
        const parts = path.replace(/^\/|\/$/g, '').split('/');
        if (parts.length === 0 || parts[0] === '') {
            return 'home';
        }
        return parts[0];
    }

    /**
     * Fetch active notification from API
     */
    async fetchActiveNotification(pageSlug) {
        try {
            const url = `${this.API_BASE}/active/?page=${encodeURIComponent(pageSlug)}`;
            const response = await fetch(url);

            if (!response.ok) {
                if (response.status === 404) return null;
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('[PromoNotification] Fetch error:', error);
            return null;
        }
    }

    /**
     * Check if notification was already seen
     */
    wasAlreadySeen(notificationId) {
        try {
            const seen = JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
            return seen.includes(notificationId);
        } catch (error) {
            return false;
        }
    }

    /**
     * Mark notification as seen
     */
    markAsSeen(notificationId) {
        try {
            const seen = JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
            if (!seen.includes(notificationId)) {
                seen.push(notificationId);
                localStorage.setItem(this.STORAGE_KEY, JSON.stringify(seen));
            }
        } catch (error) {
            console.error('[PromoNotification] localStorage write error:', error);
        }
    }

    /**
     * Create and show floating button
     */
    showFloatingButton() {
        if (this.button) return;

        this.button = document.createElement('button');
        this.button.className = 'promo-floating-button';
        this.button.textContent = this.notification.button_text;
        this.button.style.backgroundColor = this.notification.button_color;
        this.button.style.color = this.notification.text_color;
        this.button.setAttribute('aria-label', 'Show promotion');

        this.button.addEventListener('click', () => this.openModal());
        document.body.appendChild(this.button);
    }

    /**
     * Create and open modal window
     */
    openModal() {
        this.trackClick();

        this.modal = document.createElement('div');
        this.modal.className = 'promo-modal';
        this.modal.setAttribute('role', 'dialog');
        this.modal.setAttribute('aria-modal', 'true');

        const content = document.createElement('div');
        content.className = 'promo-modal-content';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'promo-modal-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.setAttribute('aria-label', 'Close');
        closeBtn.addEventListener('click', () => this.closeModal());

        const header = document.createElement('div');
        header.className = 'promo-modal-header';

        const title = document.createElement('h2');
        title.className = 'promo-modal-title';
        title.textContent = this.notification.title;

        header.appendChild(title);

        const body = document.createElement('div');
        body.className = 'promo-modal-body';

        if (this.notification.image_url) {
            const img = document.createElement('img');
            img.className = 'promo-modal-image';
            img.src = this.notification.image_url;
            img.alt = this.notification.title;
            body.appendChild(img);
        }

        const description = document.createElement('div');
        description.className = 'promo-modal-description';
        description.textContent = this.notification.description;

        body.appendChild(description);
        content.appendChild(closeBtn);
        content.appendChild(header);
        content.appendChild(body);
        this.modal.appendChild(content);
        document.body.appendChild(this.modal);

        setTimeout(() => {
            this.modal.classList.add('active');
        }, 10);

        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });

        this.handleEscKey = (e) => {
            if (e.key === 'Escape') this.closeModal();
        };
        document.addEventListener('keydown', this.handleEscKey);
    }

    /**
     * Close modal window
     */
    closeModal() {
        if (!this.modal) return;

        this.modal.classList.remove('active');

        setTimeout(() => {
            if (this.modal) {
                this.modal.remove();
                this.modal = null;
            }
        }, 400);

        if (this.handleEscKey) {
            document.removeEventListener('keydown', this.handleEscKey);
            this.handleEscKey = null;
        }

        if (this.button) {
            this.button.remove();
            this.button = null;
        }

        this.markAsSeen(this.notification.id);
    }

    /**
     * Track notification view
     */
    async trackView() {
        if (!this.notification) return;
        try {
            await fetch(`${this.API_BASE}/${this.notification.id}/track-view/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
        } catch (e) {}
    }

    /**
     * Track notification click
     */
    async trackClick() {
        if (!this.notification) return;
        try {
            await fetch(`${this.API_BASE}/${this.notification.id}/track-click/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
        } catch (e) {}
    }
}

/**
 * Optimized Initialization
 * Waits for the window to be fully loaded, then waits another 3 seconds
 * before even checking the API for promotions.
 */
window.addEventListener('load', () => {
    // Use requestIdleCallback if available to run when browser is not busy
    const initWidget = () => {
        setTimeout(() => {
            new PromoNotificationWidget().init();
        }, 3000); // 3 seconds delay after full load
    };

    if ('requestIdleCallback' in window) {
        requestIdleCallback(initWidget);
    } else {
        initWidget();
    }
});
