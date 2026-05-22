"""Tests for apps.core.ratelimit.get_client_ip — trust-bounded client-IP
resolution behind a reverse proxy."""

from django.test import RequestFactory, override_settings

from apps.core.ratelimit import get_client_ip

PROXY = "10.0.0.5"  # stands in for Traefik's container address (REMOTE_ADDR)


def _request(xff=None):
    rf = RequestFactory()
    extra = {"REMOTE_ADDR": PROXY}
    if xff is not None:
        extra["HTTP_X_FORWARDED_FOR"] = xff
    return rf.get("/", **extra)


@override_settings(TRUSTED_PROXY_HOPS=1)
def test_single_hop_returns_real_client_ip():
    assert get_client_ip(_request("203.0.113.7")) == "203.0.113.7"


@override_settings(TRUSTED_PROXY_HOPS=1)
def test_spoofed_left_hand_entries_are_ignored():
    # Client pre-seeded "1.1.1.1"; the trusted proxy appended the real IP.
    assert get_client_ip(_request("1.1.1.1, 203.0.113.7")) == "203.0.113.7"


@override_settings(TRUSTED_PROXY_HOPS=1)
def test_missing_header_falls_back_to_remote_addr():
    assert get_client_ip(_request(None)) == PROXY


@override_settings(TRUSTED_PROXY_HOPS=1)
def test_blank_header_falls_back_to_remote_addr():
    assert get_client_ip(_request("   ")) == PROXY


@override_settings(TRUSTED_PROXY_HOPS=1)
def test_non_ip_token_falls_back_to_remote_addr():
    assert get_client_ip(_request("not-an-ip-address")) == PROXY


@override_settings(TRUSTED_PROXY_HOPS=1)
def test_ipv6_client_is_accepted():
    assert get_client_ip(_request("2001:db8::1")) == "2001:db8::1"


@override_settings(TRUSTED_PROXY_HOPS=2)
def test_two_trusted_hops_selects_entry_at_minus_two():
    # client, then the CDN edge as seen by Traefik.
    assert get_client_ip(_request("203.0.113.7, 70.0.0.9")) == "203.0.113.7"


@override_settings(TRUSTED_PROXY_HOPS=2)
def test_fewer_entries_than_hops_falls_back():
    # Only one XFF entry but two trusted hops expected — chain is not as
    # configured, so trust none of it.
    assert get_client_ip(_request("203.0.113.7")) == PROXY


@override_settings(TRUSTED_PROXY_HOPS=1)
def test_always_returns_non_empty_string():
    # No REMOTE_ADDR and no header (synthetic request) still yields a value.
    req = RequestFactory().get("/")
    req.META.pop("REMOTE_ADDR", None)
    assert get_client_ip(req) == "0.0.0.0"
