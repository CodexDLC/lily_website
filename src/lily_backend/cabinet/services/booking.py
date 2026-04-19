# CODEX_DJANGO_CLI BLUEPRINT STATUS: MOVE_TO_CLI_BLUEPRINT. Reason: generated app-layer or scaffold-owned file for codex-django-cli blueprints.

from typing import Any, cast

from codex_django.booking.cabinet.types import (
    BookingChainPreviewData,
    BookingChainPreviewItem,
    BookingQuickCreateClientOption,
    BookingQuickCreateData,
    BookingQuickCreateServiceOption,
    BookingSlotPickerData,
    BookingSlotPickerOption,
    ChainPreviewSection,
    QuickCreateSection,
    SlotPickerSection,
)
from codex_django.cabinet.types.modal import (
    ActionSection,
    FormField,
    FormSection,
    KeyValueItem,
    ModalAction,
    ModalContentData,
    ModalSection,
    ProfileSection,
    SummarySection,
)
from django.db import OperationalError, ProgrammingError
from django.http import HttpRequest
from django.urls import reverse
from features.booking.booking_settings import BookingSettings
from features.booking.services.cabinet import get_booking_cabinet_workflow

from cabinet.booking_bridge import BookingActionResult, BookingModalActionState, BookingModalState, get_booking_bridge


class BookingService:
    """Page-service contract for cabinet booking pages."""

    @staticmethod
    def get_or_create_settings() -> tuple[BookingSettings, str | None]:
        """Load or initialise the singleton BookingSettings row."""
        try:
            instance, _ = BookingSettings.objects.get_or_create(pk=1)
            return instance, None
        except (OperationalError, ProgrammingError):
            return BookingSettings(), "Booking settings storage is not available yet."

    @staticmethod
    def modal_url(booking_id: int, *, mode: str | None = None) -> str:
        url = reverse("cabinet:booking_modal", kwargs={"pk": booking_id})
        return f"{url}?mode={mode}" if mode else url

    @classmethod
    def get_schedule_context(cls, request: HttpRequest) -> dict[str, Any]:
        return get_booking_cabinet_workflow().get_schedule_context(request)

    @classmethod
    def get_new_booking_context(cls, request: HttpRequest) -> dict[str, Any]:
        return get_booking_cabinet_workflow().get_new_booking_context(request)

    @classmethod
    def get_list_context(cls, request: HttpRequest, status: str | None = None) -> dict[str, Any]:
        return get_booking_cabinet_workflow().get_list_context(request, status=status)

    @classmethod
    def create_new_booking(cls, request: HttpRequest) -> dict[str, Any]:
        return get_booking_cabinet_workflow().create_new_booking(request)

    @classmethod
    def _build_modal_action(cls, booking_id: int, action: BookingModalActionState) -> ModalAction:
        if action.kind == "open_mode":
            url = cls.modal_url(booking_id, mode=action.value if action.value != "detail" else None)
            return ModalAction(
                label=action.label,
                url=url,
                method=action.method,
                style=action.style,
                icon=action.icon,
            )
        if action.kind == "execute":
            return ModalAction(
                label=action.label,
                url=reverse("cabinet:booking_action", kwargs={"pk": booking_id, "action": action.value}),
                method=action.method,
                style=action.style,
                icon=action.icon,
            )
        return ModalAction(label=action.label, method="CLOSE", style=action.style, icon=action.icon)

    @classmethod
    def _present_modal_state(cls, state: BookingModalState) -> ModalContentData:
        sections: list[ModalSection] = cast("list[ModalSection]", [])
        if state.profile:
            sections.append(
                ProfileSection(
                    name=state.profile.name,
                    subtitle=state.profile.subtitle,
                    avatar=state.profile.avatar,
                )
            )
        if state.summary_items:
            sections.append(
                SummarySection(items=[KeyValueItem(item.label, item.value) for item in state.summary_items])
            )
        if state.form and state.form.fields:
            sections.append(
                FormSection(
                    fields=[
                        FormField(
                            name=field.name,
                            label=field.label,
                            field_type=field.field_type,
                            placeholder=field.placeholder,
                            value=field.value,
                            options=field.options,
                        )
                        for field in state.form.fields
                    ]
                )
            )
        if state.slot_picker:
            sections.append(
                SlotPickerSection(
                    data=BookingSlotPickerData(
                        selected_date=state.slot_picker.selected_date,
                        selected_date_label=state.slot_picker.selected_date_label,
                        selected_time=state.slot_picker.selected_time,
                        prev_url=state.slot_picker.prev_url,
                        next_url=state.slot_picker.next_url,
                        today_url=state.slot_picker.today_url,
                        calendar_url=state.slot_picker.calendar_url,
                        slots=[
                            BookingSlotPickerOption(
                                value=slot.value,
                                label=slot.label,
                                available=slot.available,
                            )
                            for slot in state.slot_picker.slots
                        ],
                    )
                )
            )
        if state.quick_create:
            sections.append(
                QuickCreateSection(
                    data=BookingQuickCreateData(
                        resource_label=state.quick_create.prefill.resource_name,
                        date_label=state.quick_create.prefill.booking_date,
                        time_label=state.quick_create.prefill.start_time,
                        resource_id=str(state.quick_create.prefill.resource_id or ""),
                        booking_date=state.quick_create.prefill.booking_date,
                        selected_time=state.quick_create.prefill.start_time,
                        service_options=[
                            BookingQuickCreateServiceOption(
                                value=option.value,
                                label=option.label,
                                price_label=option.price_label,
                                duration_label=option.duration_label,
                            )
                            for option in state.quick_create.service_options
                        ],
                        client_options=[
                            BookingQuickCreateClientOption(
                                value=option.value,
                                label=option.label,
                                subtitle=option.subtitle,
                                email=option.email,
                                search_text=option.search_text,
                            )
                            for option in state.quick_create.client_options
                        ],
                        selected_service_id=state.quick_create.selected_service_id,
                        selected_client_id=state.quick_create.selected_client_id,
                        client_search_query=state.quick_create.client_search_query,
                        client_search_min_chars=state.quick_create.client_search_min_chars,
                        new_client_first_name=state.quick_create.new_client_first_name,
                        new_client_last_name=state.quick_create.new_client_last_name,
                        new_client_phone=state.quick_create.new_client_phone,
                        new_client_email=state.quick_create.new_client_email,
                        allow_new_client=state.quick_create.allow_new_client,
                    )
                )
            )
        if state.chain_preview:
            sections.append(
                ChainPreviewSection(
                    data=BookingChainPreviewData(
                        title=state.chain_preview.title,
                        items=[
                            BookingChainPreviewItem(
                                title=item.title,
                                subtitle=item.subtitle,
                                meta=item.meta,
                            )
                            for item in state.chain_preview.items
                        ],
                    )
                )
            )
        if state.actions:
            sections.append(
                ActionSection(actions=[cls._build_modal_action(state.booking_id, action) for action in state.actions])
            )
        return ModalContentData(title=state.title, sections=sections)

    @classmethod
    def get_booking_modal_context(cls, request: HttpRequest, booking_id: int) -> dict[str, Any]:
        mode = request.GET.get("mode", "detail")
        state = get_booking_bridge().get_modal_state(request, int(booking_id), mode)
        return {"obj": cls._present_modal_state(state)}

    @classmethod
    def perform_action(cls, request: HttpRequest, booking_id: int, action: str) -> dict[str, Any]:
        result: BookingActionResult = get_booking_bridge().execute_action(
            request=request,
            booking_id=booking_id,
            action=action,
            payload=request.POST,
        )
        return {
            "ok": result.ok,
            "code": result.code,
            "message": result.message,
            "field_errors": result.field_errors,
            "ui_effect": result.ui_effect,
            "target_url": result.target_url,
            "redirect_url": result.target_url,
        }
