# TASK-205: Admin QR Price Adjustment System

**Status:** ✅ Done (MVP Edition)
**Priority:** High
**Domain:** Booking System & Cabinet
**Estimate:** 8-10 hours

---

## Description

Implement secure QR-based price adjustment where:
1. Every new appointment receives a unique `finalize_token`.
2. A QR code is generated for the `finalize_token`.
3. The Admin/Master scans the QR code.
4. The QR code contains a direct link to the Admin Cabinet (`/cabinet/appointment/<token>/edit-price/`).
5. The Admin (logged in as staff) adjusts the **Actual Price** paid (`price_actual`).
6. Unpaid or fully past appointments are closed **automatically** by a background task.

**This replaces the concept of a complex Telegram Bot Mini App with a lightweight, secure web-based flow inside the Django Admin Cabinet.**

## Prerequisites

- [x] TASK-MVP-001 completed (basic booking works)
- [x] HTMX integrated into Admin Cabinet

## Acceptance Criteria

- [x] `Appointment.finalize_token` field added, auto-generated on save.
- [x] `Appointment.price_actual` field added to decouple quoted price from final paid price.
- [x] API endpoint / View (`AppointmentPriceEditView`) created to validate QR token.
- [x] Security: Only authenticated `is_staff` admins can view or submit the form.
- [x] Price adjustment UI in HTMX (preset buttons + custom input) implemented.
- [x] Saving the form updates `price_actual` but **does not** close the appointment.
- [ ] QR code generation pipeline integrated with `tools/media/qr_style.py`.

## Technical Details

### 1. Models

```python
# features/booking/models/appointment.py
class Appointment(models.Model):
    # ...
    price_actual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    finalize_token = models.CharField(max_length=64, unique=True, db_index=True, editable=False, null=True)
```

### 2. Django View (HTMX)

```python
# features/cabinet/views/price_adjustment.py
class AppointmentPriceEditView(AdminRequiredMixin, DetailView):
    model = Appointment
    template_name = "cabinet/appointments/edit_price.html"
    slug_url_kwarg = "token"
    slug_field = "finalize_token"
```

### 3. Automatic Closing (Background Task Concept)

Instead of manual clicking, a background worker (ARQ / Celery / Cron) marks past appointments as `Completed` automatically using the `price_actual` if provided.

## Security Features

✅ **Only authenticated Admins/Staff** can access the view.
✅ **Token-based Access:** Hard-to-guess 43-character token.
✅ **Clients are blocked:** Clients scanning the code get redirected back to their lists.

## Future Enhancements
- [ ] Connect `price_actual` to the upcoming loyalty system.
- [ ] Add `PotentialLead` tracker for unauthorized scans.
- [ ] Add automated QR display in the client-side booking summary.
