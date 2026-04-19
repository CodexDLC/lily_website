/**
 * Cookie Consent Manager - LILY Beauty Salon (v2.0 Professional)
 * GDPR/DSGVO-Compliant Cookie Consent Implementation
 */

(function() {
  'use strict';

  const STORAGE_KEY = 'cookie_consent';
  const BANNER_ID = 'cookieConsentBanner';

  // Default granular state
  const DEFAULT_CONSENT = {
    essential: true,
    analytics: false,
    marketing: false
  };

  /**
   * Updates Google Consent Mode state based on granular choices
   * @param {Object} consent - {essential, analytics, marketing}
   */
  function updateGoogleConsent(consent) {
    if (typeof gtag === 'function') {
      const gtmConsent = {
        'analytics_storage': consent.analytics ? 'granted' : 'denied',
        'ad_storage': consent.marketing ? 'granted' : 'denied',
        'ad_user_data': consent.marketing ? 'granted' : 'denied',
        'ad_personalization': consent.marketing ? 'granted' : 'denied',
        'functionality_storage': 'granted', // Always granted for site core
        'security_storage': 'granted'       // Always granted for security
      };

      gtag('consent', 'update', gtmConsent);

      // Push custom event for GTM triggers
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({
        'event': 'cookie_consent_update',
        'consent_categories': consent
      });

      console.log('[Cookie Consent] GTM Consent updated:', gtmConsent);
    }
  }

  /**
   * Saves consent choice to localStorage
   */
  function saveConsent(consent) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
    } catch (e) {
      console.error('[Cookie Consent] Storage error:', e);
    }
  }

  /**
   * Retrieves consent choice from localStorage
   */
  function getConsent() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      return null;
    }
  }

  function showBanner() {
    let banner = document.getElementById(BANNER_ID);
    if (!banner) {
      const template = document.getElementById('cookieConsentTemplate');
      if (template) {
        const clone = document.importNode(template.content, true);
        document.body.appendChild(clone);
        banner = document.getElementById(BANNER_ID);
        attachEventListeners();
      }
    }
    if (banner) {
      banner.classList.add('is-visible');
      document.body.classList.add('cookie-modal-active');
    }
  }

  function hideBanner() {
    const banner = document.getElementById(BANNER_ID);
    if (banner) {
      banner.classList.remove('is-visible');
      document.body.classList.remove('cookie-modal-active');
    }
  }

  function handleAcceptAll() {
    const consent = { essential: true, analytics: true, marketing: true };
    saveConsent(consent);
    updateGoogleConsent(consent);
    hideBanner();
  }

  function handleAcceptEssential() {
    const consent = { essential: true, analytics: false, marketing: false };
    saveConsent(consent);
    updateGoogleConsent(consent);
    hideBanner();
  }

  function handleSaveCustom() {
    const analytics = document.getElementById('cookie-check-analytics')?.checked || false;
    const marketing = document.getElementById('cookie-check-marketing')?.checked || false;
    const consent = { essential: true, analytics, marketing };
    saveConsent(consent);
    updateGoogleConsent(consent);
    hideBanner();
  }

  function toggleSettings() {
    const container = document.getElementById(BANNER_ID);
    if (container) {
      container.classList.toggle('show-settings');
    }
  }

  function attachEventListeners() {
    document.getElementById('cookieAcceptAll')?.addEventListener('click', handleAcceptAll);
    document.getElementById('cookieAcceptEssential')?.addEventListener('click', handleAcceptEssential);
    document.getElementById('cookieSaveCustom')?.addEventListener('click', handleSaveCustom);
    document.getElementById('cookieShowSettings')?.addEventListener('click', toggleSettings);
    document.getElementById('cookieBackToMain')?.addEventListener('click', toggleSettings);
  }

  function init() {
    const saved = getConsent();
    if (!saved) {
      setTimeout(showBanner, 1000); // Slight delay for better UX
    } else {
      updateGoogleConsent(saved);
    }
  }

  window.revokeCookieConsent = function() {
    const saved = getConsent() || DEFAULT_CONSENT;
    showBanner();
    // Pre-check checkboxes based on saved state
    setTimeout(() => {
      const aCheck = document.getElementById('cookie-check-analytics');
      const mCheck = document.getElementById('cookie-check-marketing');
      if (aCheck) aCheck.checked = saved.analytics;
      if (mCheck) mCheck.checked = saved.marketing;
    }, 100);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
;
