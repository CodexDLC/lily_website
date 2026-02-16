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
     * Initialize the widget
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

            // Show floating button after delay
            setTimeout(() => {
                this.showFloatingButton();
                this.trackView();
            }, data.display_delay * 1000);

        } catch (error) {
            console.error('[PromoNotification] Initialization error:', error);
        }
    }

    /**
     * Get current page slug from URL path
     * @returns {string|null} Page slug (e.g., 'home', 'services')
     */
    getCurrentPageSlug() {
        const path = window.location.pathname;

        // Remove leading/trailing slashes and split
        const parts = path.replace(/^\/|\/$/g, '').split('/');

        // Root page = 'home'
        if (parts.length === 0 || parts[0] === '') {
            return 'home';
        }

        // Return first segment (e.g., /services/ -> 'services')
        return parts[0];
    }

    /**
     * Fetch active notification from API
     * @param {string} pageSlug - Current page slug
     * @returns {Promise<Object|null>} Notification data or null
     */
    async fetchActiveNotification(pageSlug) {
        try {
            const url = `${this.API_BASE}/active/?page=${encodeURIComponent(pageSlug)}`;
            const response = await fetch(url);

            if (!response.ok) {
                // 404 = no active notifications
                if (response.status === 404) {
                    return null;
                }
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('[PromoNotification] Fetch error:', error);
            return null;
        }
    }

    /**
     * Check if notification was already seen by user
     * @param {number} notificationId - Notification ID
     * @returns {boolean} True if already seen
     */
    wasAlreadySeen(notificationId) {
        try {
            const seen = JSON.parse(localStorage.getItem(this.STORAGE_KEY) || '[]');
            return seen.includes(notificationId);
        } catch (error) {
            console.error('[PromoNotification] localStorage read error:', error);
            return false;
        }
    }

    /**
     * Mark notification as seen
     * @param {number} notificationId - Notification ID
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
        // Create button element
        this.button = document.createElement('button');
        this.button.className = 'promo-floating-button';
        this.button.textContent = this.notification.button_text;
        this.button.style.backgroundColor = this.notification.button_color;
        this.button.style.color = this.notification.text_color;
        this.button.setAttribute('aria-label', 'Открыть промо-акцию');

        // Click handler
        this.button.addEventListener('click', () => this.openModal());

        // Add to DOM
        document.body.appendChild(this.button);
    }

    /**
     * Create and open modal window
     */
    openModal() {
        // Track click
        this.trackClick();

        // Create modal overlay
        this.modal = document.createElement('div');
        this.modal.className = 'promo-modal';
        this.modal.setAttribute('role', 'dialog');
        this.modal.setAttribute('aria-modal', 'true');

        // Create modal content
        const content = document.createElement('div');
        content.className = 'promo-modal-content';

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'promo-modal-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.setAttribute('aria-label', 'Закрыть');
        closeBtn.addEventListener('click', () => this.closeModal());

        // Header
        const header = document.createElement('div');
        header.className = 'promo-modal-header';

        const title = document.createElement('h2');
        title.className = 'promo-modal-title';
        title.textContent = this.notification.title;

        header.appendChild(title);

        // Body
        const body = document.createElement('div');
        body.className = 'promo-modal-body';

        // Image (if exists)
        if (this.notification.image_url) {
            const img = document.createElement('img');
            img.className = 'promo-modal-image';
            img.src = this.notification.image_url;
            img.alt = this.notification.title;
            body.appendChild(img);
        }

        // Description
        const description = document.createElement('div');
        description.className = 'promo-modal-description';
        description.textContent = this.notification.description;

        body.appendChild(description);

        // Assemble modal
        content.appendChild(closeBtn);
        content.appendChild(header);
        content.appendChild(body);
        this.modal.appendChild(content);

        // Add to DOM
        document.body.appendChild(this.modal);

        // Trigger animation
        setTimeout(() => {
            this.modal.classList.add('active');
        }, 10);

        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Close on ESC key
        this.handleEscKey = (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        };
        document.addEventListener('keydown', this.handleEscKey);
    }

    /**
     * Close modal window
     */
    closeModal() {
        if (!this.modal) return;

        // Remove active class to trigger exit animation
        this.modal.classList.remove('active');

        // Wait for animation to finish
        setTimeout(() => {
            this.modal.remove();
            this.modal = null;
        }, 400);

        // Remove ESC key listener
        if (this.handleEscKey) {
            document.removeEventListener('keydown', this.handleEscKey);
            this.handleEscKey = null;
        }

        // Hide floating button and mark as seen
        if (this.button) {
            this.button.remove();
            this.button = null;
        }

        this.markAsSeen(this.notification.id);
    }

    /**
     * Track notification view (button shown)
     */
    async trackView() {
        if (!this.notification) return;

        try {
            await fetch(`${this.API_BASE}/${this.notification.id}/track-view/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
        } catch (error) {
            console.error('[PromoNotification] Track view error:', error);
        }
    }

    /**
     * Track notification click (modal opened)
     */
    async trackClick() {
        if (!this.notification) return;

        try {
            await fetch(`${this.API_BASE}/${this.notification.id}/track-click/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
        } catch (error) {
            console.error('[PromoNotification] Track click error:', error);
        }
    }
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PromoNotificationWidget().init();
    });
} else {
    // DOM already loaded
    new PromoNotificationWidget().init();
}
