# 📜 Sitemaps Configuration (`sitemaps.py`)

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../README.md)

This `sitemaps.py` module defines the sitemap configurations for the Django backend application. It includes a sitemap for static pages and integrates sitemaps from other features (e.g., categories), allowing search engines to efficiently crawl and index the website's content.

The static sitemap should stay thin and library-backed. Generic multilingual sitemap behavior belongs to `codex_django.core.sitemaps`, while Lily owns only the project settings and feature-specific sitemap registrations.

## Purpose

The module centralizes the definition of sitemaps, which are XML files that list the URLs of a site. Sitemaps help search engines discover all the pages on a website, especially those that might not be found through regular crawling.

## `StaticSitemap` Class

```python
from codex_django.core.sitemaps import StaticPagesSitemap


class StaticSitemap(StaticPagesSitemap):
    pass
```

### Description

This sitemap generates entries for static pages of the website by using the shared Codex sitemap base.

### Attributes

*   `priority = 0.8`:
    Inherited default priority for these URLs relative to other URLs on the site.
*   `changefreq = "monthly"`:
    Inherited default hint for how frequently the content at these URLs is likely to change.

### Methods

*   `items()`:
    Reads view names from `SITEMAP_STATIC_PAGES`.
*   `location(self, item)`:
    Inherited from the library base. It reverses route names directly, then checks `SITEMAP_LOOKUP_NAMESPACES`.

## Lily-Owned Settings

The project keeps sitemap policy in settings:

```python
SITEMAP_STATIC_PAGES = [
    "home",
    "services",
    "team",
    "contacts",
    "faq",
    "buchungsregeln",
    "impressum",
    "datenschutz",
]

SITEMAP_DEFAULT_LANGUAGE = "de"
SITEMAP_LOOKUP_NAMESPACES = ["booking"]
```

`SITEMAP_DEFAULT_LANGUAGE` controls the `x-default` alternate URL. `SITEMAP_LOOKUP_NAMESPACES` lets string sitemap items resolve through project namespaces without copying sitemap URL logic.

## `sitemaps` Dictionary

```python
sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
}
```

### Description

This dictionary aggregates all sitemap classes into a single object that can be passed to Django's sitemap view.

### Contents

*   `"static"`: Maps the key `static` to the `StaticSitemap` class.
*   `"categories"`: Maps the key `categories` to the `CategorySitemap` class, which is imported from `features.main.sitemaps`. This indicates that the `main` feature provides its own sitemap for categories.

## Usage

The `sitemaps` dictionary is imported into the root `urls.py` (`core/urls.py`) and passed to Django's `sitemap` view:

```python
path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
```
This configuration makes the sitemap accessible at `/sitemap.xml`.

## Example for Model-Based Sitemaps (Commented Out)

The module also includes commented-out example code for how to create sitemaps for Django models (e.g., `ServiceSitemap`), demonstrating how to define `changefreq`, `priority`, `items()`, and `lastmod()` methods for dynamic content.
