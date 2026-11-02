---
name: lily-selector-service-discipline
description: Change Lily read/context paths, mutations and workflow integration while preserving existing application adapters. Use for booking or messaging behavior and data assembly, not visual-only edits.
---

# Lily Read and Write Paths

Prefer selectors for new query composition and services/workflows for mutations, transactions and side effects. Keep domain queries and workflow decisions out of templates. This is a change guideline, not a claim that all existing views already follow it.

Locate the actual path before choosing a filename. Lily uses `src/lily_backend/features/booking/selector/` and `features/conversations/selector/` (singular), but `src/lily_backend/system/selectors/` (plural). Do not create a parallel directory to normalize naming.

Existing `src/lily_backend/cabinet/services/` also contains page/context services. For example, `BookingService.get_schedule_context()` delegates to the booking cabinet workflow. Preserve that public page contract rather than moving every read out of a service as incidental cleanup.

- Booking changes: read [booking integration](references/booking-integration.md) for the current provider, engine and persistence seams.
- Conversations: trace `src/lily_backend/features/conversations/selector/`, `services/workflow.py`, `services/threads.py` and `services/campaign_service.py` according to the affected operation. Preserve the existing notification/job path instead of adding a second dispatch from a view.
- Shared client data: inspect `src/lily_backend/system/selectors/client_profile.py` and `system/services/client_profile.py`.

For new read selectors, avoid writes. For workflow changes, preserve authorization, transaction boundaries and side-effect timing; do not infer safety from a method name. Verify changed filters/context through selector or page-service tests and changed mutations through state/side-effect tests. Use repository verification guidance for the handoff.
