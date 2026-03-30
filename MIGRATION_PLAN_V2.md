# Lily Website 2.0 Migration Master Plan

## Approval Rule

This document is the master migration plan for the `2.0` transition.

Mandatory rule:
- Each major stage listed below must produce its own separate implementation plan before active development starts.
- That implementation plan must be reviewed and explicitly approved step by step before work on that stage begins.
- If a stage reveals a meaningful architectural divergence, the stage pauses and is re-planned before coding continues.

## Executive Summary

The migration target is not a rewrite of the whole site and not a rewrite of `codex-django`.
The goal is to migrate `lily_website` to the platform base and reusable building blocks already present in `codex-django`, while keeping the site behavior stable and protecting booking and client data.

We are allowed to refactor the project aggressively where needed, including:
- replacing the local `codex_tools` project layer,
- restructuring `system`,
- replacing the old cabinet,
- redesigning internal Django model structure for masters and schedules.

The hard safety boundary is:
- do not lose or corrupt client data,
- do not lose or corrupt booking history / appointments.

## Core Principles

- Safety has priority over architectural purity.
- The library provides bricks; the building is assembled in the project.
- We do not force project code to stay legacy just to avoid refactoring.
- We can rewrite project internals if this reduces long-term hacks.
- Template rendering contracts may change if needed; site visual layout and CSS approach should stay intact.
- Owner/admin cabinet moves first.
- Client registration and branded client cabinet come later.

## Key Risks

1. Data loss or broken references in client and appointment tables during schema migration.
2. Booking regressions when replacing local `codex_tools` booking runtime with `codex-django` booking adapters/selectors.
3. Cabinet regressions during full replacement of the old cabinet.
4. Partial migration state where some runtime paths still use local `codex_tools`.
5. Hidden template/context regressions after moving to new `system`/`core` contracts.
6. Weak regression coverage before the main refactor starts.

## Stage 0 - Stabilization Baseline

Goal:
- Freeze current behavior before migration work starts.

What moves:
- Smoke matrix for all public pages (home, services, team, contacts, legal).
- Integration tests for the full booking flow (slot selection → appointment create → confirm → complete).
- Integration tests for reschedule and cancel flows.
- Baseline checks for cabinet dashboard and core CRUD operations (appointments, clients, masters).
- Fixture-based tests for context processors (site_settings, static_content).

What does not move:
- No platform migration yet.

Risks:
- Low.

Dependencies:
- None.

Adapter/selector layer:
- No.

Can be a separate branch:
- Yes.

Done criteria:
- Public page smoke tests are green.
- Booking flow integration tests cover create, confirm, reschedule, cancel, complete.
- Cabinet baseline tests cover dashboard rendering and key CRUD views.
- Context processor tests verify template variable contracts.
- All baseline tests are green and documented as the regression reference for subsequent stages.

## Stage 1 - Platform Bootstrap in Project

Goal:
- Attach `lily_website` to the platform stack and prepare the project for migration.

What moves:
- Dependency wiring to `codex-django` and ecosystem packages.
- `CODEX_*` settings contracts.
- Project-level migration flags.
- Initial replacement path for local `codex_tools`.

What does not move:
- No booking behavior switch yet.

Risks:
- Medium.

Dependencies:
- Stage 0.

Adapter/selector layer:
- Yes.

Can be a separate branch:
- Yes.

Done criteria:
- Project boots with platform dependencies.
- Runtime still matches baseline behavior.
- Migration flags allow controlled cutover.

## Stage 2 - Data-Safe Schema Migration

Goal:
- Normalize project-owned structures that are safe to refactor, especially masters and schedules.

What moves:
- Drop `work_days` JSONField on Master and replace with `AbstractWorkingDay` relational model (from `codex-django`).
- The new table supports per-weekday schedule entries and multi-day ranges (covers both regular schedule and vacation/time-off periods).
- Current `work_days` data is minimal (effectively one record) — safe to clear and recreate directly in the new table, no complex data migration needed.
- Refactor master-related structures as needed.
- Refactor system-side tables where safe.

What does not move:
- Do not risk destructive changes to clients and booking history.

Risks:
- High.

Dependencies:
- Stage 1.

Adapter/selector layer:
- Temporary, for controlled transition.

Can be a separate branch:
- Yes.

Done criteria:
- Appointments still reference masters correctly.
- Client and booking history remain intact.
- New `WorkingDay` table is created and replaces the old JSONField.
- `DjangoAvailabilityAdapter` reads schedule from the new relational model.
- Old `work_days` JSONField is removed from Master.

## Stage 3 - Core/System Cutover

Goal:
- Move the project onto platform-style `core` and `system` usage while keeping the public site visually stable.

What moves:
- Context processors.
- SEO/static/system wiring.
- Cache and redis integration.
- Top-level `system` alignment.

What does not move:
- No visual redesign of the public site.

Risks:
- Medium.

Dependencies:
- Stage 2.

Adapter/selector layer:
- Yes, but should shrink during the stage.

Can be a separate branch:
- Yes.

Done criteria:
- Public site renders correctly.
- Template variable changes are completed safely.
- System layer no longer depends on legacy project hacks.

## Stage 4 - Booking Engine Cutover

Goal:
- Fully replace local booking runtime with `codex-django` booking adapters/selectors.

What moves:
- Engine layer: local `codex_tools.booking` engine (SlotCalculator, ChainFinder) → `codex-services` (via `codex-django` adapters and selectors).
- Adapter layer: local `DjangoAvailabilityAdapter` → `codex_django.booking.DjangoAvailabilityAdapter`.
- Booking selectors: local slot service → `codex_django.booking.selectors` (get_available_slots, get_calendar_data, etc.).
- Exception mapping and transaction path.

What stays as project code:
- `BookingService` (v1) and `BookingV2Service` — these are project-level orchestration, not engine logic.
- `BookingScorer` weights and project-specific scoring configuration.
- Appointment creation, confirmation, cancellation business rules.

What does not move:
- No redesign of booking UX.
- No product-level booking 2.0 expansion.

Risks:
- Very high.

Dependencies:
- Stage 3.

Adapter/selector layer:
- Yes, this is the target architecture for booking integration.

Can be a separate branch:
- Yes.

Done criteria:
- Snapshot tests: slot generation results from `codex-services` engine match baseline results for documented scenarios.
- Booking create/reschedule/cancel/confirm flows are green.
- Local `src/backend_django/codex_tools/booking` engine code is removed from runtime use.
- Project-level booking services (`BookingService`, `BookingV2Service`) work with the new engine layer.

## Stage 5 - Cabinet Replacement (Owner/Admin First)

Goal:
- Replace the old cabinet with the new cabinet approach for owner/admin work.

What moves:
- New owner/admin cabinet shell.
- Dashboard and owner actions.
- New cabinet routing and access flow.

What does not move:
- Full client-facing cabinet.
- Public registration UX.

Risks:
- High.

Dependencies:
- Stage 4.

Adapter/selector layer:
- Yes, for project-owned dashboard widgets and actions.

Can be a separate branch:
- Yes.

Done criteria:
- Owner/admin operations work in the new cabinet.
- Old cabinet runtime path is removable.

## Stage 6 - Client Model Evolution

Goal:
- Keep shadow-client behavior and prepare optional registration without breaking current booking flow.

What moves:
- Expansion of client model or profile layer.
- Preparation for future registration/auth flows.
- Future-compatible magic-link path.

What does not move:
- Full branded client cabinet rollout.

Risks:
- Medium.

Dependencies:
- Stage 5.

Adapter/selector layer:
- Optional.

Can be a separate branch:
- Yes.

Done criteria:
- Current client booking identity remains stable.
- Registration-ready extension exists without forcing user/password flow immediately.

## Stage 7 - Hardening and Release Path

Goal:
- Finish phase one safely through local validation, dev loop, and only then push/production.

What moves:
- Final cleanup.
- Final checks.
- Controlled enablement of new runtime path.

What does not move:
- Deferred product work from later phases.

Risks:
- Medium.

Dependencies:
- Stages 0 through 6.

Adapter/selector layer:
- Only if still needed as temporary fallback.

Can be a separate branch:
- Yes.

Done criteria:
- Local full run passes.
- Dev loop passes.
- Production push happens only after dev stabilization.

## Branch Strategy

- Long-running branch: `codex/2.0-platform-migration`
- Each major stage may also have its own child branch when implementation starts.
- Merge points are allowed only after the approved implementation plan for that stage is completed and validated.

## Deferred Scope

- Full booking UX redesign.
- Hybrid booking/ecommerce/cart logic.
- Promo/combo product refactor.
- Full branded client cabinet.
- Full env-to-database migration for settings and API keys.
