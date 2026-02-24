import contextlib
import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from features.booking.models.appointment import Appointment
from features.main.models.category import Category
from loguru import logger as log

from ..decorators import tma_secure_required


@csrf_exempt
@tma_secure_required
def appointments_view(request):
    """
    TMA страница: список записей по категории.
    GET  — рендер списка с пагинацией.
    POST — actions: confirm / cancel / update.
    """
    req_id = request.GET.get("req_id") or request.POST.get("req_id")
    ts = request.GET.get("ts") or request.POST.get("ts")
    sig = request.GET.get("sig") or request.POST.get("sig")

    # --- POST: действия над записями ---
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        action = data.get("action")
        appointment_id = data.get("appointment_id")

        if not action or not appointment_id:
            return JsonResponse({"status": "error", "message": "Missing action or appointment_id"}, status=400)

        try:
            appt = Appointment.objects.get(id=appointment_id)

            if action == "confirm":
                appt.status = Appointment.STATUS_CONFIRMED
                appt.save()
                log.info(f"TMA Appointments | #{appointment_id} confirmed")
                return JsonResponse({"status": "success", "message": "Запись подтверждена"})

            elif action == "cancel":
                appt.status = Appointment.STATUS_CANCELLED
                appt.save()
                log.info(f"TMA Appointments | #{appointment_id} cancelled")
                return JsonResponse({"status": "success", "message": "Запись отменена"})

            elif action == "update":
                # Допустимые статусы
                allowed_statuses = [s[0] for s in Appointment.STATUS_CHOICES] + ["no_show"]
                new_status = data.get("status")
                if new_status and new_status in allowed_statuses:
                    appt.status = new_status
                price = data.get("price")
                if price is not None:
                    with contextlib.suppress(ValueError, TypeError):
                        appt.price = float(price)
                admin_notes = data.get("admin_notes")
                if admin_notes is not None:
                    appt.admin_notes = admin_notes
                cancel_reason = data.get("cancel_reason")
                if cancel_reason is not None:
                    appt.cancel_reason = cancel_reason
                appt.save()
                log.info(f"TMA Appointments | #{appointment_id} updated: status={appt.status}")
                return JsonResponse({"status": "success"})

            else:
                return JsonResponse({"status": "error", "message": "Invalid action"}, status=400)

        except Appointment.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Запись не найдена"}, status=404)
        except Exception as e:
            log.error(f"TMA Appointments | Error processing action {action}: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # --- GET: рендер списка ---
    category_slug = request.GET.get("category", "")
    try:
        page_num = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page_num = 1

    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        category = None

    qs = (
        Appointment.objects.filter(service__category__slug=category_slug)
        .select_related("client", "service", "master")
        .order_by("-datetime_start")
    )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page_num)

    context = {
        "req_id": req_id,
        "ts": ts,
        "sig": sig,
        "category": category,
        "category_slug": category_slug,
        "page_obj": page_obj,
        "page_num": page_num,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count,
    }
    return render(request, "telegram_app/appointments.html", context)
