"""Cabinet authentication views: login, logout, magic link."""

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views import View


class CabinetLoginView(View):
    template_name = "cabinet/auth/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return _redirect_by_role(request)
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return _redirect_by_role(request)
        return render(request, self.template_name, {"error": "Неверный логин или пароль."})


class CabinetLogoutView(View):
    def get(self, request):
        request.session.pop("cabinet_client_id", None)
        logout(request)
        return redirect("home")

    def post(self, request):
        return self.get(request)


class MagicLinkView(View):
    """Login via access_token from SMS/Email link."""

    template_name = "cabinet/auth/magic_link.html"

    def get(self, request, token):
        from features.booking.models import Client

        client = Client.objects.filter(access_token=token).first()
        if not client:
            return render(request, self.template_name, {"error": "Ссылка недействительна или устарела."})

        # If client has a linked Django user — log in as that user
        if client.user:
            login(request, client.user)
        else:
            # Guest: store client_id in session (no Django user required)
            request.session["cabinet_client_id"] = client.pk

        return redirect("cabinet:appointments")


def _redirect_by_role(request):
    if request.user.is_staff:
        return redirect("cabinet:dashboard")
    return redirect("cabinet:appointments")
