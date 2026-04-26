# Lily — Extracting EmailSettings from SiteSettings

This is the lily-specific application of
`codex-django/docs/dev/messaging/05_settings_migration.md`. Read that
first for the abstract recipe.

## Inventory of fields to move

`SiteSettings` today inherits these mixins from codex-django:

* `AbstractSiteSettings`
* `SiteContactSettingsMixin`
* `SiteEmailIdentityMixin` ← **fully moves to AbstractEmailSettings**
* `SiteGeoSettingsMixin`
* `SiteMarketingSettingsMixin`
* `SiteTechnicalSettingsMixin`
* `SiteSocialSettingsMixin`

Plus locally-declared fields (`system/models/settings.py`):

* `company_name`, `owner_name`, `tax_number` — stay
* `site_base_url`, `logo_url` — **move**
* `telegram_bot_username` — stays
* `working_hours_*` — stays
* `price_range` — stays
* `url_path_*` (4 fields) — **move**

After migration:

* `SiteSettings` no longer inherits `SiteEmailIdentityMixin`.
* `SiteSettings` loses `site_base_url`, `logo_url`, `url_path_*`
  fields.
* New `EmailSettings` model in `features/messaging/`.

## Step-by-step migration

### Step 1 — add the abstract mixin in codex-django

(Library work, see codex-django doc 05.)

### Step 2 — create `EmailSettings` in lily

```python
# src/lily_backend/features/messaging/messaging_settings.py
from codex_django.messaging.mixins import (
    AbstractEmailSettings,
    EmailSettingsSyncMixin,
)


class EmailSettings(AbstractEmailSettings, EmailSettingsSyncMixin):
    """Lily-specific email identity + URL paths singleton."""

    class Meta:
        verbose_name = "Email Settings"
        verbose_name_plural = "Email Settings"
```

Add to `INSTALLED_APPS` if `features.messaging` is not already a
configured app (it will be after the rename — see doc 03).

### Step 3 — Django migrations

Two-step migration, atomic on the data side:

#### Migration A — create the new model + copy data

```python
# features/messaging/migrations/0001_initial.py
from django.db import migrations, models


def copy_from_site_settings(apps, schema_editor):
    SiteSettings = apps.get_model("system", "SiteSettings")
    EmailSettings = apps.get_model("messaging", "EmailSettings")

    site = SiteSettings.objects.filter(pk=1).first()
    if site is None:
        return

    EmailSettings.objects.update_or_create(
        pk=1,
        defaults={
            "email_from":             getattr(site, "email_from", "") or "",
            "email_sender_name":      getattr(site, "email_sender_name", "") or "",
            "email_reply_to":         getattr(site, "email_reply_to", "") or "",
            "site_base_url":          getattr(site, "site_base_url", "") or "",
            "logo_url":               getattr(site, "logo_url", "") or "",
            "url_path_confirm":       getattr(site, "url_path_confirm", "") or "",
            "url_path_cancel":        getattr(site, "url_path_cancel", "") or "",
            "url_path_reschedule":    getattr(site, "url_path_reschedule", "") or "",
            "url_path_contact_form":  getattr(site, "url_path_contact_form", "") or "",
        },
    )


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ("system", "0001_initial"),    # whatever the latest is
    ]

    operations = [
        migrations.CreateModel(
            name="EmailSettings",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("email_from",        models.EmailField(max_length=254)),
                ("email_sender_name", models.CharField(max_length=128)),
                ("email_reply_to",    models.EmailField(blank=True, max_length=254)),
                ("site_base_url",     models.URLField()),
                ("logo_url",          models.CharField(blank=True, max_length=255)),
                ("url_path_confirm",       models.CharField(blank=True, max_length=255)),
                ("url_path_cancel",        models.CharField(blank=True, max_length=255)),
                ("url_path_reschedule",    models.CharField(blank=True, max_length=255)),
                ("url_path_contact_form",  models.CharField(blank=True, max_length=255)),
            ],
            options={"verbose_name": "Email Settings", "verbose_name_plural": "Email Settings"},
        ),
        migrations.RunPython(copy_from_site_settings, migrations.RunPython.noop),
    ]
```

#### Migration B — remove fields from SiteSettings

This must be a **separate migration** so that production can roll back
to migration A if a regression is found in step 5 (consumer updates).

```python
# system/migrations/00XX_remove_email_fields_from_sitesettings.py
class Migration(migrations.Migration):
    dependencies = [
        ("system", "0001_initial"),
        ("messaging", "0001_initial"),
    ]
    operations = [
        # Remove from SiteEmailIdentityMixin (the mixin that's removed from SiteSettings):
        migrations.RemoveField("system", "SiteSettings", "email_from"),
        migrations.RemoveField("system", "SiteSettings", "email_sender_name"),
        migrations.RemoveField("system", "SiteSettings", "email_reply_to"),
        # Remove locally-declared fields:
        migrations.RemoveField("system", "SiteSettings", "site_base_url"),
        migrations.RemoveField("system", "SiteSettings", "logo_url"),
        migrations.RemoveField("system", "SiteSettings", "url_path_confirm"),
        migrations.RemoveField("system", "SiteSettings", "url_path_cancel"),
        migrations.RemoveField("system", "SiteSettings", "url_path_reschedule"),
        migrations.RemoveField("system", "SiteSettings", "url_path_contact_form"),
    ]
```

Also remove `SiteEmailIdentityMixin` from `SiteSettings.__bases__`:

```python
# system/models/settings.py
class SiteSettings(
    AbstractSiteSettings,
    SiteContactSettingsMixin,
    # SiteEmailIdentityMixin,  ← REMOVED
    SiteGeoSettingsMixin,
    SiteMarketingSettingsMixin,
    SiteTechnicalSettingsMixin,
    SiteSocialSettingsMixin,
):
    ...
```

### Step 4 — update consumers

Find every read of the moved fields:

```bash
grep -rn "SiteSettings" src/lily_backend/ \
  | grep -E "\.(email_from|email_sender_name|email_reply_to|site_base_url|logo_url|url_path_confirm|url_path_cancel|url_path_reschedule|url_path_contact_form)"
```

Known call sites:

* `features/booking/services/notifications.py:25` — reads
  `site_base_url`, `logo_url`. Switch to
  `EmailSettings.load().site_base_url` etc.
* `cabinet/views/site_settings.py:21` — reads all SiteSettings.
  Update to drop the moved fields from the view's serialization.
* `system/admin/settings.py:101-102` — admin form. Remove fields from
  the form (they're now visible only in the messaging cabinet
  settings page).
* Anywhere a Django template renders `{{ site.email_from }}` etc. —
  switch to a context processor that exposes `email_settings`.

A small helper in `features/messaging/utils.py`:

```python
from features.messaging.messaging_settings import EmailSettings

def email_settings():
    return EmailSettings.load()
```

So consumer code becomes:

```python
from features.messaging.utils import email_settings

es = email_settings()
context["site_url"] = es.site_base_url
```

### Step 5 — Redis sync rename

Worker reads from a Redis hash named `site_settings:` today (see
`src/workers/core/site_settings.py:40-45`). Two changes:

1. Rename the hash to `email_settings:`.
2. The Django writer (`DjangoSiteSettingsManager` in codex-django)
   currently writes the whole `SiteSettings.to_dict()` to Redis. The
   migration replaces this writer for the moved fields with a
   dedicated `EmailSettingsRedisManager` triggered by
   `EmailSettingsSyncMixin.save()`.

During the deprecation window, the writer writes both keys:

* `site_settings:` — still includes `email_*`, `url_path_*`,
  `site_base_url`, `logo_url` (until removed).
* `email_settings:` — the new singular key.

The worker reader prefers `email_settings:`, falls back to
`site_settings:`. After deprecation (next minor release), only the
new key is written.

### Step 6 — cabinet wiring

After the cabinet rename (doc 03), the
`MessagingSettingsView` at `/cabinet/messaging/settings/` is the only
UI for editing these fields. Until the rename ships, ship a
temporary "Email" tab inside the existing site-settings cabinet that
points at `EmailSettings.load()`. Users see the same inputs they had
before, but they're now stored in a different table. Once doc 03
lands, that temporary tab is removed.

## Rollback

* If migration B goes bad, run it in reverse — fields are restored
  from a previous DB backup. The fields on `SiteSettings` are gone;
  there is no automatic re-copy.
* If migration A goes bad, drop the `EmailSettings` table. No data
  loss because the source is still in `SiteSettings`.

The split migration into A and B exists to make this rollback clean.

## Verification

* `python manage.py migrate` succeeds.
* `EmailSettings.load()` returns the values that were on
  `SiteSettings` before the migration.
* Booking and conversation emails still send and contain correct
  links (the hostname comes from `site_base_url`, the logo from
  `logo_url`).
* The Redis hash `email_settings:` is populated after a save.
* Worker reads from `email_settings:` after restart and uses
  `email_sender_name` correctly (verified by SendGrid fallback test —
  see doc 04).
