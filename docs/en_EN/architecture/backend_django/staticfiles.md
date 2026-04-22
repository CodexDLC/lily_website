# 📜 Staticfiles Directory

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../README.md)

This directory (`src/backend_django/staticfiles`) is the designated location where Django's `collectstatic` management command gathers all static files (CSS, JavaScript, images, etc.) from installed applications and other configured locations.

## Purpose

The `staticfiles` directory serves as a centralized repository for all static assets that need to be served directly by a web server (like Nginx) in a production environment. During development, Django can serve static files, but in production, it's more efficient for a dedicated web server to handle them.

## Contents

This directory is typically empty in the source code repository. Its contents are populated dynamically during the deployment process when `python manage.py collectstatic` is executed.

Example contents after `collectstatic`:
```
staticfiles/
├── admin/
│   ├── css/
│   ├── img/
│   └── js/
├── css/
├── js/
└── img/
```

## Usage

*   **Development:** In a local development setup (e.g., using `docker compose up`), this directory might be mounted as a volume to allow `collectstatic` to write to it.
*   **Production:** In production, after `collectstatic` is run (often during the Docker image build or deployment script), this directory's contents are typically served by Nginx. The `deploy/nginx/site.conf` and `deploy/nginx/site-local.conf` configurations include `alias` directives to serve files from this location.
