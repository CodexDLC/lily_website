// PWA Enhancement для LILY Admin
// Улучшения для мобильного опыта и PWA функциональности

(function() {
    'use strict';

    console.log('🚀 LILY Admin PWA Enhancement загружен');

    // ========================================
    // ОПРЕДЕЛЕНИЕ PWA MODE
    // ========================================

    const isPWA = window.matchMedia('(display-mode: standalone)').matches ||
                  window.navigator.standalone === true ||
                  document.referrer.includes('android-app://');

    if (isPWA) {
        console.log('✅ Запущено как PWA');
        document.body.classList.add('pwa-mode');
    } else {
        console.log('🌐 Запущено в браузере');
    }

    // ========================================
    // PULL TO REFRESH
    // ========================================

    let touchStartY = 0;
    let touchMoveY = 0;
    const pullToRefreshThreshold = 80;
    let isRefreshing = false;

    document.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
        touchMoveY = e.touches[0].clientY;
        const pullDistance = touchMoveY - touchStartY;

        if (window.scrollY === 0 && pullDistance > 0 && !isRefreshing) {
            showPullIndicator(pullDistance);
        }
    }, { passive: true });

    document.addEventListener('touchend', () => {
        const pullDistance = touchMoveY - touchStartY;

        if (pullDistance > pullToRefreshThreshold && window.scrollY === 0 && !isRefreshing) {
            isRefreshing = true;
            hidePullIndicator();
            showToast('🔄 Обновление...', 'info');

            setTimeout(() => {
                window.location.reload();
            }, 300);
        } else {
            hidePullIndicator();
        }

        touchStartY = 0;
        touchMoveY = 0;
    });

    function showPullIndicator(distance) {
        let indicator = document.querySelector('.ptr-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'ptr-indicator';
            indicator.textContent = '⬇️ Потяните для обновления';
            document.body.appendChild(indicator);
        }

        if (distance > pullToRefreshThreshold) {
            indicator.textContent = '⬆️ Отпустите для обновления';
        } else {
            indicator.textContent = '⬇️ Потяните для обновления';
        }

        indicator.classList.add('active');
    }

    function hidePullIndicator() {
        const indicator = document.querySelector('.ptr-indicator');
        if (indicator) {
            indicator.classList.remove('active');
        }
    }

    // ========================================
    // BOTTOM NAVIGATION
    // ========================================

    if (window.innerWidth <= 768) {
        createBottomNav();
    }

    function createBottomNav() {
        // Проверяем, не создана ли уже навигация
        if (document.querySelector('.pwa-bottom-nav')) {
            return;
        }

        const currentPath = window.location.pathname;

        const bottomNav = document.createElement('div');
        bottomNav.className = 'pwa-bottom-nav';
        bottomNav.innerHTML = `
            <a href="/admin/" class="${currentPath === '/admin/' || currentPath === '/admin' ? 'active' : ''}">
                <span class="material-icons">dashboard</span>
                <span>Главная</span>
            </a>
            <a href="/admin/booking/appointment/" class="${currentPath.includes('appointment') ? 'active' : ''}">
                <span class="material-icons">calendar_month</span>
                <span>Записи</span>
            </a>
            <a href="/admin/booking/master/" class="${currentPath.includes('master') ? 'active' : ''}">
                <span class="material-icons">face</span>
                <span>Мастера</span>
            </a>
            <a href="/admin/booking/client/" class="${currentPath.includes('client') ? 'active' : ''}">
                <span class="material-icons">group</span>
                <span>Клиенты</span>
            </a>
        `;

        document.body.appendChild(bottomNav);
        console.log('📱 Bottom Navigation создана');
    }

    // ========================================
    // ONLINE/OFFLINE ИНДИКАТОР
    // ========================================

    window.addEventListener('online', () => {
        console.log('✅ Подключение восстановлено');
        showToast('✅ Подключение восстановлено', 'success');
    });

    window.addEventListener('offline', () => {
        console.log('⚠️ Нет подключения к сети');
        showToast('⚠️ Нет подключения к сети', 'warning');
    });

    // ========================================
    // TOAST NOTIFICATIONS
    // ========================================

    function showToast(message, type = 'info') {
        // Удаляем предыдущие toast'ы
        const existingToasts = document.querySelectorAll('.pwa-toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `pwa-toast ${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideDown 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Экспорт для глобального использования
    window.showToast = showToast;

    // ========================================
    // HAPTIC FEEDBACK
    // ========================================

    if ('vibrate' in navigator) {
        document.addEventListener('click', (e) => {
            const target = e.target.closest('button, a.button, input[type="submit"], .submit-row input');
            if (target) {
                navigator.vibrate(10);
            }
        }, { passive: true });

        console.log('📳 Haptic feedback включен');
    }

    // ========================================
    // SERVICE WORKER UPDATES
    // ========================================

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(registration => {
            console.log('✅ Service Worker готов');

            // Проверка обновлений каждые 30 минут
            setInterval(() => {
                registration.update();
            }, 30 * 60 * 1000);
        });

        // Обработка обновлений Service Worker
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            console.log('🔄 Service Worker обновлен');
            showToast('Доступна новая версия приложения', 'info');
        });
    }

    // ========================================
    // SCREEN ORIENTATION
    // ========================================

    if (screen.orientation) {
        screen.orientation.addEventListener('change', () => {
            console.log('🔄 Ориентация изменена:', screen.orientation.type);

            // Пересоздать bottom nav при изменении ориентации
            const existingNav = document.querySelector('.pwa-bottom-nav');
            if (existingNav && window.innerWidth <= 768) {
                existingNav.remove();
                setTimeout(createBottomNav, 100);
            }
        });
    }

    // ========================================
    // FORM VALIDATION IMPROVEMENTS
    // ========================================

    document.addEventListener('invalid', (e) => {
        e.preventDefault();
        const input = e.target;

        // Показать красивое сообщение об ошибке
        if (input.validity.valueMissing) {
            showToast('⚠️ Заполните обязательное поле', 'warning');
        } else if (input.validity.typeMismatch) {
            showToast('⚠️ Неверный формат данных', 'warning');
        } else {
            showToast('⚠️ Проверьте правильность заполнения формы', 'warning');
        }

        // Скролл к полю с ошибкой
        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        input.focus();
    }, true);

    // ========================================
    // PREVENT ZOOM ON DOUBLE TAP
    // ========================================

    let lastTouchEnd = 0;
    document.addEventListener('touchend', (e) => {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            e.preventDefault();
        }
        lastTouchEnd = now;
    }, { passive: false });

    // ========================================
    // KEYBOARD HELPERS
    // ========================================

    // Скрывать клавиатуру при scroll
    let isScrolling;
    window.addEventListener('scroll', () => {
        clearTimeout(isScrolling);
        isScrolling = setTimeout(() => {
            if (document.activeElement.tagName === 'INPUT' ||
                document.activeElement.tagName === 'TEXTAREA') {
                // Не делаем blur - пользователь может скроллить, продолжая набирать
            }
        }, 150);
    }, { passive: true });

    // ========================================
    // PERFORMANCE MONITORING
    // ========================================

    if (window.performance && window.performance.timing) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = window.performance.timing;
                const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                console.log(`⚡ Время загрузки страницы: ${pageLoadTime}ms`);

                if (pageLoadTime > 3000) {
                    console.warn('⚠️ Медленная загрузка страницы');
                }
            }, 0);
        });
    }

    // ========================================
    // NETWORK INFORMATION API
    // ========================================

    if ('connection' in navigator) {
        const connection = navigator.connection;

        function logConnectionInfo() {
            console.log(`📶 Тип соединения: ${connection.effectiveType}`);
            console.log(`📊 Downlink: ${connection.downlink} Mbps`);

            // Показываем предупреждение на медленном соединении
            if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                showToast('⚠️ Медленное подключение', 'warning');
            }
        }

        connection.addEventListener('change', logConnectionInfo);
        logConnectionInfo();
    }

    // ========================================
    // VISIBILITY API
    // ========================================

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('👋 Приложение свернуто');
        } else {
            console.log('👀 Приложение открыто');

            // Проверяем обновления при возврате
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.ready.then(registration => {
                    registration.update();
                });
            }
        }
    });

    // ========================================
    // SAFE AREA INSETS (для iOS)
    // ========================================

    function updateSafeAreaInsets() {
        const root = document.documentElement;

        if (CSS.supports('padding-top: env(safe-area-inset-top)')) {
            console.log('📱 Safe area insets поддерживаются');
        }
    }

    updateSafeAreaInsets();

    // ========================================
    // DEBUG INFO
    // ========================================

    console.log('📱 User Agent:', navigator.userAgent);
    console.log('📐 Размер экрана:', `${window.innerWidth}x${window.innerHeight}`);
    console.log('🎨 Pixel Ratio:', window.devicePixelRatio);
    console.log('🌐 Online:', navigator.onLine);
    console.log('💾 Storage:', 'localStorage' in window);

    // ========================================
    // ГОТОВО
    // ========================================

    console.log('✅ PWA Enhancement инициализирован');

})();
