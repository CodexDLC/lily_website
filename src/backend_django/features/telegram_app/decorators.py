from functools import wraps

from django.http import HttpResponseForbidden

from .services.security import validate_hmac_signature, validate_telegram_init_data


def tma_secure_required(view_func):
    """
    Decorator to ensure the view is accessed securely via Telegram Mini App.
    It expects 'req_id', 'ts', and 'sig' in GET parameters for initial load.
    It may also look for 'tgWebAppData' in headers or POST data.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Validate HMAC signature from URL
        req_id = request.GET.get("req_id")
        timestamp = request.GET.get("ts")
        signature = request.GET.get("sig")

        if not req_id or not timestamp or not signature:
            return HttpResponseForbidden("Missing security parameters.")

        if not validate_hmac_signature(req_id, timestamp, signature):
            return HttpResponseForbidden("Invalid signature.")

        # 2. Validate Telegram InitData if provided
        # In a real scenario, the first GET hits the page, and the JS then sends POSTs
        # with initData. We might only strictly validate initData on POST or via JS.
        # But if it's passed in query params (less common), we can check it.
        # Often, we check initData on the actual form submission endpoint.

        if request.method == "POST":
            # Assume initData is sent in POST body or headers
            init_data = request.headers.get("X-Telegram-Init-Data") or request.POST.get("initData")
            if not validate_telegram_init_data(init_data):
                return HttpResponseForbidden("Invalid Telegram authentication data.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
