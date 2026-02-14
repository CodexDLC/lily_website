from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView, View
from loguru import logger

# Предполагаем, что у вас есть некий сервис для работы с токенами в Redis
# from src.shared.core.redis_service import RedisService # Пример
# redis_service = RedisService(...) # Инициализация где-то в зависимостях


class ConfirmAppointmentView(TemplateView):
    template_name = "booking/confirm_appointment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get("token")
        logger.info(f"ConfirmAppointmentView accessed with token: {token}")
        # Здесь будет логика:
        # 1. Найти токен в Redis
        # 2. Если найден, подтвердить запись
        # 3. Удалить токен
        # 4. Если не найден или истек, показать ошибку
        context["token"] = token
        return context


class CancelAppointmentView(TemplateView):
    template_name = "booking/cancel_appointment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get("token")
        logger.info(f"CancelAppointmentView accessed with token: {token}")
        context["token"] = token
        return context


class CancelAppointmentActionView(View):
    """
    Обрабатывает POST-запрос на фактическую отмену после подтверждения на странице.
    """

    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        logger.info(f"CancelAppointmentActionView POST received for token: {token}")
        # Здесь будет логика:
        # 1. Найти токен в Redis
        # 2. Если найден, отменить запись
        # 3. Удалить токен
        # 4. Перенаправить на страницу успеха/ошибки
        # Пока просто редирект на главную
        # return redirect(reverse("home"))
        return render(request, "booking/cancel_success.html", {"token": token})  # Пример страницы успеха


class RescheduleAppointmentView(TemplateView):
    template_name = "booking/reschedule_appointment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get("token")
        slot_id = self.request.GET.get("slot_id")  # Если токен слота пришел как GET-параметр
        logger.info(f"RescheduleAppointmentView accessed with token: {token}, slot_id: {slot_id}")
        # Здесь будет логика:
        # 1. Найти токен в Redis
        # 2. Если найден, показать форму переноса, возможно, с предзаполненным слотом
        context["token"] = token
        context["slot_id"] = slot_id
        return context


# Пример страницы успеха для отмены
class CancelSuccessView(TemplateView):
    template_name = "booking/cancel_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["token"] = kwargs.get("token")
        return context
