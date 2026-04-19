/**
 * Cookie Consent Manager - LILY Beauty Salon
 * GDPR/DSGVO-Compliant Cookie Consent Implementation
 *
 * Features:
 * - Google Consent Mode v2 integration
 * - localStorage persistence
 * - GTM DataLayer events for custom triggers
 * - Consent revocation support
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'cookie_consent';
  const BANNER_ID = 'cookieConsentBanner';
  const ACCEPT_BTN_ID = 'cookieAccept';
  const REJECT_BTN_ID = 'cookieReject';

  /**
   * Updates Google Consent Mode state
   * @param {string} consentValue - 'granted' or 'denied'
   */
  function updateGoogleConsent(consentValue) {
    if (typeof gtag === 'function') {
      gtag('consent', 'update', {
        'ad_storage': consentValue,
        'ad_user_data': consentValue,
        'ad_personalization': consentValue,
        'analytics_storage': consentValue
      });

      // Push event to DataLayer for GTM triggers
      if (consentValue === 'granted') {
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({
          'event': 'cookie_consent_update',
          'consent_status': 'granted'
        });
      }

      console.log('[Cookie Consent] Google Consent updated:', consentValue);
    } else {
      console.warn('[Cookie Consent] gtag() not available');
    }
  }

  /**
   * Saves consent choice to localStorage
   * @param {string} choice - 'granted' or 'denied'
   */
  function saveConsent(choice) {
    try {
      localStorage.setItem(STORAGE_KEY, choice);
      console.log('[Cookie Consent] Saved to localStorage:', choice);
    } catch (e) {
      console.error('[Cookie Consent] Failed to save to localStorage:', e);
    }
  }

  /**
   * Retrieves consent choice from localStorage
   * @returns {string|null} - 'granted', 'denied', or null
   */
  function getConsent() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      console.error('[Cookie Consent] Failed to read from localStorage:', e);
      return null;
    }
  }

  /**
   * Shows the cookie consent banner
   */
  function showBanner() {
    let banner = document.getElementById(BANNER_ID);

    // If banner not in DOM, inject it from template
    if (!banner) {
      const template = document.getElementById('cookieConsentTemplate');
      if (template) {
        // Use standard <template> API — works reliably on all mobile browsers
        const clone = document.importNode(template.content, true);
        document.body.appendChild(clone);
        banner = document.getElementById(BANNER_ID);

        // After injection, we MUST attach listeners to the new buttons
        attachEventListeners();
        console.log('[Cookie Consent] Banner injected from template');
      } else {
        console.error('[Cookie Consent] Template #cookieConsentTemplate not found');
        return;
      }
    }

    if (banner) {
      banner.style.display = 'block';
      console.log('[Cookie Consent] Banner displayed');
    }
  }

  /**
   * Hides the cookie consent banner
   */
  function hideBanner() {
    const banner = document.getElementById(BANNER_ID);
    if (banner) {
      banner.style.display = 'none';
      console.log('[Cookie Consent] Banner hidden');
    }
  }

  /**
   * Handles "Accept All" button click
   */
  function handleAccept() {
    console.log('[Cookie Consent] User accepted cookies');
    saveConsent('granted');
    updateGoogleConsent('granted');
    hideBanner();
  }

  /**
   * Handles "Only Essential" button click
   */
  function handleReject() {
    console.log('[Cookie Consent] User rejected cookies (only essential)');
    saveConsent('denied');
    // Consent remains 'denied' as set in _analytics_head.html
    hideBanner();
  }

  /**
   * Attaches click handlers to banner buttons
   */
  function attachEventListeners() {
    const acceptBtn = document.getElementById(ACCEPT_BTN_ID);
    const rejectBtn = document.getElementById(REJECT_BTN_ID);

    if (acceptBtn) {
      // Use removeEventListener first to avoid double binding if called multiple times
      acceptBtn.removeEventListener('click', handleAccept);
      acceptBtn.addEventListener('click', handleAccept);
    }

    if (rejectBtn) {
      rejectBtn.removeEventListener('click', handleReject);
      rejectBtn.addEventListener('click', handleReject);
    }
  }

  /**
   * Initializes the cookie consent manager
   */
  function init() {
    const savedConsent = getConsent();

    // If no consent decision yet, show banner (this will trigger injection)
    if (!savedConsent) {
      showBanner();
    } else {
      console.log('[Cookie Consent] Existing consent found:', savedConsent);
      // We still might want to attach listeners if revokeCookieConsent is used later
      // but revokeCookieConsent calls showBanner() which handles it.
    }
  }

  /**
   * Public API for revoking consent (called from footer link)
   */
  window.revokeCookieConsent = function() {
    console.log('[Cookie Consent] Consent revocation requested');
    localStorage.removeItem(STORAGE_KEY);
    showBanner();
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  console.log('[Cookie Consent] Manager loaded');
})();
