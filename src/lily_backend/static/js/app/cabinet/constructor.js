/**
 * LILY Booking Constructor V2 — Frontend Logic
 */

function filterServices(category, el) {
    // Update UI tabs
    document.querySelectorAll('.filter-btn').forEach(t => t.classList.remove('active'));
    if (el) el.classList.add('active');

    // Update hidden input for HTMX
    const input = document.getElementById('current-category-val');
    if (input) input.value = category;

    // Filter cards visibility
    const searchInput = document.getElementById('service-search-input');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

    document.querySelectorAll('.service-card-v2').forEach(item => {
        let isVisible = (category === 'all' || item.dataset.category === category);

        // If there's an active text search, apply it too
        if (isVisible && query.length >= 3) {
            const titleElement = item.querySelector('.svc-title');
            const title = titleElement ? titleElement.textContent.toLowerCase() : '';
            isVisible = title.includes(query);
        }

        item.style.display = isVisible ? 'flex' : 'none';
    });
}

function filterServicesByText(searchText) {
    const query = searchText.toLowerCase().trim();
    const category = document.getElementById('current-category-val')?.value || 'all';

    document.querySelectorAll('.service-card-v2').forEach(item => {
        // First check category visibility
        const isCategoryMatch = category === 'all' || item.dataset.category === category;

        if (!isCategoryMatch) {
            item.style.display = 'none';
            return;
        }

        // If query length is less than 3, just respect the category filter
        if (query.length < 3) {
            item.style.display = 'flex';
            return;
        }

        const titleElement = item.querySelector('.svc-title');
        const title = titleElement ? titleElement.textContent.toLowerCase() : '';

        if (title.includes(query)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

function selectDate(el) {
    if (el.classList.contains('disabled')) return;
    document.querySelectorAll('.cal-day-v2').forEach(d => d.classList.remove('active'));
    el.classList.add('active');
}

function selectTime(time, el) {
    // Highlight selected slot
    document.querySelectorAll('.slot-btn').forEach(p => p.classList.remove('active'));
    if (el) el.classList.add('active');

    // Update summary panel
    const summaryTime = document.getElementById('summary-time');
    if (summaryTime) summaryTime.textContent = time;

    // Update hidden input for confirmation
    const timeInput = document.getElementById('selected-time-val');
    if (timeInput) timeInput.value = time;

    // Enable confirm button
    const confirmBtn = document.getElementById('confirm-booking-btn');
    if (confirmBtn) confirmBtn.disabled = false;
}

function fillClient(phone, firstName, lastName, id, email) {
    // Fill form fields
    const fields = {
        'client-phone': phone,
        'client-email': email || '',
        'client-first-name': firstName,
        'client-last-name': lastName,
        'client-search-input': firstName + ' ' + lastName
    };

    for (const [id, value] of Object.entries(fields)) {
        const el = document.getElementById(id);
        if (el) el.value = value;
    }

    // Clear search results
    const results = document.getElementById('client-search-results');
    if (results) results.innerHTML = '';
}

// HTMX Event Listeners
document.body.addEventListener('htmx:afterRequest', function(evt) {
    // Reset summary time if date was changed
    if (evt.detail.requestConfig.vals && evt.detail.requestConfig.vals.action === 'select_date') {
        const summaryDate = document.getElementById('summary-date');
        const summaryTime = document.getElementById('summary-time');
        const timeInput = document.getElementById('selected-time-val');
        const confirmBtn = document.getElementById('confirm-booking-btn');

        if (summaryDate) summaryDate.textContent = evt.detail.requestConfig.vals.date;
        if (summaryTime) summaryTime.textContent = '--';
        if (timeInput) timeInput.value = '';
        if (confirmBtn) confirmBtn.disabled = true;
    }
});
