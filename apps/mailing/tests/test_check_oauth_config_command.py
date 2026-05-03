"""Tests for `python manage.py check_oauth_config`.

The command is the deploy-time guardrail: it must exit non-zero if the
Microsoft tenant discovery URL is unreachable so CI/CD can gate on it.
"""
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command


def test_check_oauth_config_exits_non_zero_on_bad_microsoft_tenant(settings, capsys):
    settings.MICROSOFT_TENANT = "definitely-not-a-real-tenant"

    bad_ms = MagicMock(status_code=400)
    ok_google = MagicMock(status_code=400)  # 4xx from Google is fine — endpoint is reachable

    def fake_get(url, *a, **kw):
        return bad_ms

    def fake_post(url, *a, **kw):
        return ok_google

    with patch("apps.mailing.management.commands.check_oauth_config.requests.get",
               side_effect=fake_get), \
         patch("apps.mailing.management.commands.check_oauth_config.requests.post",
               side_effect=fake_post):
        with pytest.raises(SystemExit) as excinfo:
            call_command("check_oauth_config")

    assert excinfo.value.code != 0
    captured = capsys.readouterr()
    assert "Microsoft tenant" in captured.err
    assert "definitely-not-a-real-tenant" in captured.err


def test_check_oauth_config_succeeds_when_both_endpoints_reachable(settings, capsys):
    settings.MICROSOFT_TENANT = "common"

    ok_ms = MagicMock(status_code=200)
    ok_google = MagicMock(status_code=400)

    with patch("apps.mailing.management.commands.check_oauth_config.requests.get",
               return_value=ok_ms), \
         patch("apps.mailing.management.commands.check_oauth_config.requests.post",
               return_value=ok_google):
        # Should NOT raise SystemExit.
        call_command("check_oauth_config")

    captured = capsys.readouterr()
    assert "OK Microsoft tenant" in captured.out
    assert "OK Google token endpoint" in captured.out


def test_check_oauth_config_exits_non_zero_when_microsoft_unreachable(settings, capsys):
    """Network error talking to Microsoft must also fail the deploy gate."""
    import requests as _r
    settings.MICROSOFT_TENANT = "common"

    ok_google = MagicMock(status_code=400)

    with patch("apps.mailing.management.commands.check_oauth_config.requests.get",
               side_effect=_r.ConnectionError("dns")), \
         patch("apps.mailing.management.commands.check_oauth_config.requests.post",
               return_value=ok_google):
        with pytest.raises(SystemExit) as excinfo:
            call_command("check_oauth_config")

    assert excinfo.value.code != 0
    captured = capsys.readouterr()
    assert "unreachable" in captured.err
