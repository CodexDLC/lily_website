import pytest
from features.conversations.campaigns.audience import AudienceFilter
from features.conversations.selector.audience import DjangoAudienceBuilder
from system.models import Client


@pytest.mark.django_db
def test_audience_filter_to_from_dict():
    f = AudienceFilter(email_opt_in=True, has_valid_email=False)
    d = f.to_dict()
    f2 = AudienceFilter.from_dict(d)
    assert f2.email_opt_in is True
    assert f2.has_valid_email is False


@pytest.mark.django_db
def test_django_audience_builder_count():
    Client.objects.all().delete()
    import uuid

    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    Client.objects.create(email=f"{uid1}@example.com", consent_marketing=True)
    Client.objects.create(email=f"{uid2}@example.com", consent_marketing=False)
    Client.objects.create(email=None, consent_marketing=True)

    builder = DjangoAudienceBuilder()

    print(f"DEBUG: All clients: {list(Client.objects.values_list('email', 'consent_marketing'))}")

    # Opt-in only
    count1 = builder.count(AudienceFilter(email_opt_in=True, has_valid_email=False))
    print(f"DEBUG: Count 1: {count1}")
    assert count1 == 2

    # Valid email only
    count2 = builder.count(AudienceFilter(email_opt_in=False, has_valid_email=True))
    print(f"DEBUG: Count 2: {count2}")
    assert count2 == 2
