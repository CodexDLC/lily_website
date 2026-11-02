import html
import json
import re
from contextlib import contextmanager
from html.parser import HTMLParser

import pytest
from codex_platform.redis_service.operations.sync_hash import SyncHashOperations
from core.static_content_manager import ProjectStaticContentManager
from django.utils.html import strip_tags
from system.models import StaticTranslation


_JSON_LD_PATTERN = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL,
)
_TITLE_PATTERN = re.compile(r"<title>(.*?)</title>", re.DOTALL)
_LANGUAGES = ("de", "en", "ru", "uk")
_PUBLIC_PATHS = (
    "",
    "contacts/",
    "services/",
    "team/",
    "impressum/",
    "datenschutz/",
    "faq/",
    "buchungsregeln/",
    "booking/",
)
_ACCOUNT_PATHS = (
    "accounts/login/",
    "accounts/signup/",
    "accounts/password/reset/",
    "cabinet/login/",
)
_REQUIRED_HREFLANGS = {"de", "en", "ru", "uk", "x-default"}


class _AnchorAuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._anchor_attrs: dict[str, str | None] | None = None
        self._anchor_text: list[str] = []
        self.empty_anchors: list[str] = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a":
            self._anchor_attrs = attributes
            self._anchor_text = []
        elif tag == "img" and self._anchor_attrs is not None:
            self._anchor_text.append(attributes.get("alt") or "")

    def handle_data(self, data):
        if self._anchor_attrs is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or self._anchor_attrs is None:
            return
        accessible_name = "".join(self._anchor_text).strip()
        accessible_name = accessible_name or (self._anchor_attrs.get("aria-label") or "").strip()
        accessible_name = accessible_name or (self._anchor_attrs.get("title") or "").strip()
        if not accessible_name:
            self.empty_anchors.append(self._anchor_attrs.get("href") or "<missing href>")
        self._anchor_attrs = None
        self._anchor_text = []


def _assert_valid_seo_markup(content: str) -> None:
    assert content.count("<title>") == 1
    assert content.count('rel="canonical"') == 1
    assert _REQUIRED_HREFLANGS <= set(re.findall(r'hreflang="([^"]+)"', content))

    for block in _JSON_LD_PATTERN.findall(content):
        json.loads(html.unescape(block))

    parser = _AnchorAuditParser()
    parser.feed(content)
    assert parser.empty_anchors == []


@pytest.mark.integration
@pytest.mark.parametrize("language", _LANGUAGES)
def test_public_pages_render_valid_unique_seo_markup(client, language):
    titles = []

    for path in _PUBLIC_PATHS:
        response = client.get(f"/{language}/{path}")

        assert response.status_code == 200
        content = response.content.decode()
        _assert_valid_seo_markup(content)
        titles.append(html.unescape(_TITLE_PATTERN.search(content).group(1)).strip())

    assert len(titles) == len(set(titles))


@pytest.mark.integration
@pytest.mark.parametrize("language", _LANGUAGES)
@pytest.mark.parametrize("path", _ACCOUNT_PATHS)
def test_account_pages_are_not_indexable(client, language, path):
    response = client.get(f"/{language}/{path}")

    assert response.status_code == 200
    assert response.content.count(b"<title>") == 1
    assert response.content.count(b'<meta name="robots" content="noindex, nofollow">') == 1


@pytest.mark.integration
@pytest.mark.parametrize("language", _LANGUAGES)
def test_service_detail_renders_valid_seo_markup(client, language, service, master):
    service.masters.add(master)

    response = client.get(f"/{language}/services/{service.category.slug}/")

    assert response.status_code == 200
    _assert_valid_seo_markup(response.content.decode())


@pytest.mark.integration
@pytest.mark.parametrize("language", _LANGUAGES)
def test_faq_json_ld_escapes_database_content(
    client,
    fake_sync_redis,
    language,
    monkeypatch,
    settings,
):
    settings.CODEX_REDIS_ENABLED = True
    unsafe_text = 'Absage mit <b>HTML</b>, "Anführungszeichen", \\ und\nZeilenumbruch.'
    translation = StaticTranslation.objects.create(
        key="faq_a5_schema",
        content=unsafe_text,
        content_de=unsafe_text,
        content_en=unsafe_text,
        content_ru=unsafe_text,
        content_uk=unsafe_text,
    )
    translation.refresh_from_db()
    expected_text = strip_tags(getattr(translation, f"content_{language}"))

    @contextmanager
    def fake_sync_hash(_manager):
        yield SyncHashOperations(fake_sync_redis)

    monkeypatch.setattr(ProjectStaticContentManager, "sync_hash", fake_sync_hash)

    response = client.get(f"/{language}/faq/")

    assert response.status_code == 200
    blocks = _JSON_LD_PATTERN.findall(response.content.decode())
    assert blocks
    schemas = [json.loads(html.unescape(block)) for block in blocks]
    faq_schema = next(schema for schema in schemas if schema.get("@type") == "FAQPage")
    answers = [item["acceptedAnswer"]["text"] for item in faq_schema["mainEntity"]]
    assert expected_text in answers


@pytest.mark.integration
@pytest.mark.parametrize("language", _LANGUAGES)
def test_legacy_contact_url_permanently_redirects_with_language(client, language):
    response = client.get(f"/{language}/conversations/contact/")

    assert response.status_code == 301
    assert response.url == f"/{language}/contacts/"
