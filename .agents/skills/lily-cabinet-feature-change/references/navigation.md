# Lily Cabinet Navigation Wiring

Read for registration, module selection or startup behavior. Paths below are relative to `src/lily_backend/`.

| Registration source | Responsibility |
| --- | --- |
| `features/booking/cabinet.py` | `booking` and `staff`; booking settings use `settings_url` |
| `features/conversations/cabinet.py` | Inbox/campaign navigation, unread notification and message metrics |
| `features/main/cabinet.py` | `catalog` shell and dynamic service-category sidebar |
| `features/notifications/cabinet.py` | Notification-log view in `ops`, guarded by `system.view_sitesettings` |
| `system/cabinet.py` | Shared spaces, users, business statistics, ops and dashboard registrations |

Follow the existing `TopbarEntry`/`SidebarItem` declarations for the affected module. Preserve `settings_url` as the bottom settings destination; do not add a duplicate ordinary sidebar item. Module identifiers are runtime keys, not necessarily folder names (`business_stats` is one example).

Catalog startup is intentionally database-free: `features/main/apps.py` calls `register_catalog_shell()` in `ready()`. Dynamic categories refresh on category save/delete and after migrations. Preserve that split; do not query categories during application startup. `tests/lily_backend/unit/test_main_cabinet.py` at repository root exercises this registration behavior.

For vendor API changes, consult documentation or the usage skill matching the installed `codex-django` version. This map describes Lily's registrations, not the complete library API.
