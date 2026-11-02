---
name: lily-static-assets
description: Maintain Lily public and cabinet CSS/JS source bundles, compiler configuration and static collection boundaries. Use for asset changes, not backend-only work.
---

# Lily Static Assets

Paths are relative to the repository root.

| Bundle | Source/config location | Generated output |
| --- | --- | --- |
| Public CSS | `src/lily_backend/static/css/base.css` and adjacent `compiler_config.json` | `src/lily_backend/static/css/app.css` |
| Cabinet CSS | `src/lily_backend/cabinet/static/cabinet/css/base.css` and adjacent `compiler_config.json` | `src/lily_backend/cabinet/static/cabinet/css/app_cabinet.css` |
| Cabinet local JS | `src/lily_backend/cabinet/static/cabinet/js/compiler_config.json`; entry `app/cabinet.entry.js`, roots `core`, `widgets`, `builders` relative to that config | `src/lily_backend/cabinet/static/cabinet/js/app/cabinet_local.js` |

Edit the owning source bundle and rebuild; do not hand-edit generated outputs. Keep public source/styles separate from cabinet source/styles. Add shared behavior through the established owning component rather than cross-importing the two bundles casually.

The library's `cabinet/js/app/cabinet.js` is distinct from Lily's `cabinet_local.js`. `tests/lily_backend/unit/test_cabinet_library_assets.py` also checks library ownership of Alpine. Do not vendor or overwrite those managed assets as a local bundle fix.

With the existing project environment, run from the repository root:

```powershell
uv run python src/lily_backend/manage.py compile_assets
```

The command handles configured public and app static bundles. Inspect the resulting diff and confirm the requested source change appears in its intended output. Do not rebuild assets just for editing these instructions.

Before changing collection paths read `src/lily_backend/core/settings/modules/static.py`: source CSS directories are excluded through `STATICFILES_IGNORE_PATTERNS`, while compiled bundles are runtime artifacts. Verify the affected rendered page and static resolution after a path change; follow repository verification guidance for code changes.
