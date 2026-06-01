---
name: lily-static-assets
description: Load this skill when changing Lily CSS, JavaScript, static files, compiler_config.json, public app.css, cabinet app_cabinet.css, cabinet_local.js, asset compilation, or staticfiles behavior.
---

# Lily Static Assets

Use this for CSS/JS/static asset changes.

## Asset bundles

Lily has separate public and cabinet asset bundles.

Public site CSS:

- source entry: `src/lily_backend/static/css/base.css`
- config: `src/lily_backend/static/css/compiler_config.json`
- compiled output: `src/lily_backend/static/css/app.css`
- loaded by public templates through `{% static 'css/app.css' %}`

Cabinet CSS:

- source entry: `src/lily_backend/cabinet/static/cabinet/css/base.css`
- config: `src/lily_backend/cabinet/static/cabinet/css/compiler_config.json`
- compiled output: `src/lily_backend/cabinet/static/cabinet/css/app_cabinet.css`

Cabinet JS:

- config: `src/lily_backend/cabinet/static/cabinet/js/compiler_config.json`
- compiled output: `src/lily_backend/cabinet/static/cabinet/js/app/cabinet_local.js`
- source roots include `core`, `widgets`, and `builders`

## Do not edit compiled outputs

Do not manually edit:

- `src/lily_backend/static/css/app.css`
- `src/lily_backend/cabinet/static/cabinet/css/app_cabinet.css`
- generated cabinet JS outputs when they are built from compiler config

Edit source files and run compilation.

## Public vs cabinet separation

- Public CSS belongs under `src/lily_backend/static/css/...`.
- Cabinet CSS belongs under `src/lily_backend/cabinet/static/cabinet/css/...`.
- Public site templates should not depend on cabinet CSS classes.
- Cabinet templates should not depend on public marketing CSS.
- Shared visual ideas must be copied intentionally into the correct source bundle, not imported across bundles casually.

## Compilation

Use Django's asset command:

```powershell
$env:UV_CACHE_DIR='.uv-cache'; uv run python src\lily_backend\manage.py compile_assets
```

The command scans `compiler_config.json` files in static dirs and app static dirs.

Prefer `manage.py compile_assets` because it handles both public and cabinet assets.

## Staticfiles ignore behavior

Source CSS directories are ignored by staticfiles collection. The compiled bundle is the runtime artifact.

Check `src/lily_backend/core/settings/modules/static.py` before changing source/output paths.

## Change workflow

1. Identify whether the change is public or cabinet.
2. Edit source CSS/JS under the correct source bundle.
3. If adding a new source entry/root, update the correct `compiler_config.json`.
4. Run `compile_assets`.
5. Verify the compiled output changed as expected.

## CSS guidance

- Prefer existing component/page/layout files over one-off inline styles.
- Keep page-specific CSS in page files and reusable controls in component files.
- Avoid putting cabinet-only styling in public source folders.
- Avoid putting public marketing styling in cabinet source folders.
