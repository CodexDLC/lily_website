from typing import Any

from django import forms
from django.db.models import QuerySet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView, UpdateView
from features.main.models import Service, ServiceCategory

from cabinet.mixins import StaffRequiredMixin


class ServiceQuickEditForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["price", "duration", "price_info", "duration_info"]
        widgets = {
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "duration": forms.NumberInput(attrs={"class": "form-control"}),
            "price_info": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. ab 45 €"}),
            "duration_info": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 60-90 Min"}),
        }


class ServicesListView(StaffRequiredMixin, ListView):
    """List services, optionally filtered by category in sidebar."""

    model = Service
    template_name = "cabinet/services/list.html"
    context_object_name = "services"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        request.cabinet_module = "catalog"
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Service]:
        qs = super().get_queryset().filter(is_active=True).order_by("category__order", "order")
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get("category_slug")
        active_category = None
        if category_slug:
            active_category = ServiceCategory.objects.filter(slug=category_slug).first()

        ctx.update(
            {
                "active_category": active_category,
                "total_services_count": Service.objects.filter(is_active=True).count(),
            }
        )
        return ctx


class ServiceQuickEditView(StaffRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceQuickEditForm
    template_name = "cabinet/services/includes/quick_edit_form.html"

    def form_valid(self, form: Any) -> Any:
        self.object = form.save()
        return JsonResponse({"status": "ok", "message": "Service updated successfully", "refresh": True})

    def form_invalid(self, form: Any) -> Any:
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


class CategoryStatusToggleView(StaffRequiredMixin, View):
    """Toggle is_active or is_planned for a category via HTMX."""

    def post(self, request: Any, pk: int) -> HttpResponse:
        category = get_object_or_404(ServiceCategory, pk=pk)
        field = request.POST.get("field")

        if field in ["is_active", "is_planned"]:
            current_val = getattr(category, field)
            setattr(category, field, not current_val)
            category.save()

        return render(
            request,
            "cabinet/services/includes/category_toggles.html",
            {"active_category": category},
        )
