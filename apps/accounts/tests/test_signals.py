"""Tests for the accounts app signal handlers."""
import pytest
from allauth.socialaccount.signals import social_account_removed


@pytest.mark.django_db
def test_unlinking_social_account_pauses_active_campaign(google_linked_user):
    social = google_linked_user.socialaccount_set.first()
    assert google_linked_user.is_campaign_active is True

    social_account_removed.send(sender=None, request=None, socialaccount=social)

    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False


@pytest.mark.django_db
def test_unlinking_does_not_touch_already_paused_campaign(google_linked_user):
    google_linked_user.is_campaign_active = False
    google_linked_user.save(update_fields=["is_campaign_active"])

    social = google_linked_user.socialaccount_set.first()
    social_account_removed.send(sender=None, request=None, socialaccount=social)

    google_linked_user.refresh_from_db()
    assert google_linked_user.is_campaign_active is False
