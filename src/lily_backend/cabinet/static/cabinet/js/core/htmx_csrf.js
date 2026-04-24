/* CODEX_DJANGO_CLI BLUEPRINT STATUS: MOVE_TO_CLI_BLUEPRINT. Reason: generated cabinet app asset source for codex-django-cli blueprints. */
/* @provides cabinet.core.htmx_csrf
   @depends cabinet.core.dom */
(function (window, document) {
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.content) return meta.content;

        const input = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (input && input.value) return input.value;

        // Prefer the longest csrftoken* cookie name to avoid stale duplicates
        // left by legacy deploys (e.g. "csrftoken" vs renamed "csrftoken_app").
        let best = null;
        const re = /(?:^|;\s*)(csrftoken[^=]*)=([^;]+)/g;
        let match;
        while ((match = re.exec(document.cookie)) !== null) {
            if (!best || match[1].length > best[0].length) {
                best = [match[1], match[2]];
            }
        }
        return best ? decodeURIComponent(best[1]) : null;
    }

    document.addEventListener('htmx:configRequest', function (evt) {
        const method = evt.detail.verb.toUpperCase();
        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
            const token = getCsrfToken();
            if (token) {
                evt.detail.headers['X-CSRFToken'] = token;
            }
        }
    });
})(window, document);
