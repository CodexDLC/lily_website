from typing import TYPE_CHECKING, Any

from core.logger import log
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

if TYPE_CHECKING:
    from features.booking.dto import BookingState

from features.booking.selectors import wizard as wizard_selectors
from features.booking.services.booking import BookingService
from features.booking.services.session import BookingSessionService
from features.booking.views.steps import CalendarStep, ConfirmStep, MasterStep, ServiceStep


class BookingWizardView(TemplateView):
    template_name = "booking/wizard.html"

    # Map step numbers to Step Classes
    STEP_CLASSES = {
        "1": ServiceStep,
        "2": MasterStep,
        "3": CalendarStep,
        "4": ConfirmStep,
    }

    def get(self, request, *args, **kwargs):
        session_service = BookingSessionService(request)

        # 1. Update state from request params
        session_service.update_from_request(request.GET)

        # 2. Get the typed state object
        state: BookingState = session_service.get_state()

        # 3. Determine current step
        current_step = str(state.step)

        # 4. Get Step Class & Object
        step_class = self.STEP_CLASSES.get(current_step, ServiceStep)
        step_obj = step_class(state, request)

        # 5. Get Context
        try:
            step_context = step_obj.get_context()
        except Exception as e:
            log.error(f"Error getting context for step {current_step}: {e}", exc_info=True)
            # Don't clear session, just fallback to step 1
            return redirect("booking_wizard")

        if step_context is None:
            log.warning(f"Missing data for step {current_step}, falling back to previous step")
            # If step 3 (Calendar) fails, go to step 2 (Masters)
            if state.step > 1:
                state.step -= 1
                session_service.save_state(state)
                return redirect("booking_wizard")

            session_service.clear()
            return redirect("booking_wizard")

        # 6. Prepare Full Context
        context: dict[str, Any] = {"steps": wizard_selectors.get_stepper_context(state.step), **step_context}

        # 7. Render
        if request.headers.get("HX-Request"):
            return render(request, step_obj.template_name, context)

        context["current_step_template"] = step_obj.template_name
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle final booking submission."""
        log.info("Processing booking submission...")

        session_service = BookingSessionService(request)

        # 1. Get Data
        state = session_service.get_state()
        form_data = {
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "phone": request.POST.get("phone"),
            "email": request.POST.get("email"),
            "request_call": request.POST.get("request_call") == "on",
            "client_notes": request.POST.get("client_notes", ""),
        }

        # 2. Create Appointment
        appointment = BookingService.create_appointment(state, form_data)

        if not appointment:
            log.error(f"Failed to create appointment for state: {state}")
            # Clear session so user can start fresh
            session_service.clear()
            return render(request, "500.html", status=500)

        # 3. Clear Session
        session_service.clear()

        # 4. Return Success
        return render(request, "booking/steps/step_5_success.html", {"appointment": appointment})
