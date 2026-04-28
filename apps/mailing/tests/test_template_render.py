"""H11 regression tests: EmailTemplate.render uses a restricted Formatter
that strips attribute / item access from placeholders, and a SafeDict that
leaves unknown keys as literal `{name}` text.

Why these matter:
  - `{cv_url.__class__.__mro__[1]}`-style payloads in a stored template can
    walk Python's object graph via `str.format`'s spec mini-language. The
    restricted formatter renders the bare `cv_url` value instead.
  - A typo like `{compay_name}` in a template used to raise `KeyError` and
    mark every queued send FAILED. Now it renders the placeholder literally
    so ops can spot the mistake without dropping the campaign.
"""
import pytest

from apps.mailing.models import EmailTemplate


def _render(subject="", body=""):
    t = EmailTemplate(subject=subject, body_html=body)
    return t.render(company_name="Acme", cv_url="http://cv", unsubscribe_url="http://u")


@pytest.mark.django_db
def test_known_placeholders_resolve_to_values():
    s, b = _render(subject="hi {company_name}", body="cv: {cv_url}, u: {unsubscribe_url}")
    assert s == "hi Acme"
    assert b == "cv: http://cv, u: http://u"


@pytest.mark.django_db
def test_unknown_placeholder_renders_as_literal_text():
    """Acceptance for the SafeDict half of H11."""
    _, b = _render(body="hello {typo_name}")
    assert b == "hello {typo_name}"


@pytest.mark.django_db
def test_attribute_walk_falls_back_to_bare_value():
    """Acceptance for H11: a template with `{cv_url.__class__}` renders as
    the literal value, not the type repr — attribute access is disabled."""
    _, b = _render(body="leak: {cv_url.__class__}")
    # Without the fix this would render `<class 'str'>`.
    assert b == "leak: http://cv"


@pytest.mark.django_db
def test_nested_attribute_walk_is_disabled():
    """Defence-in-depth: chained attribute access (the actual exploit
    payload mentioned in security-fixes.md §2.3) doesn't leak either."""
    _, b = _render(body="{cv_url.__class__.__mro__[1]}")
    assert b == "http://cv"


@pytest.mark.django_db
def test_index_access_is_disabled():
    """Bracket-indexing into a value is the other half of `format`'s
    mini-language. The fix strips `[...]` like it strips `.attr`."""
    _, b = _render(body="first char: {cv_url[0]}")
    assert b == "first char: http://cv"


# H14: body_html has a 50 000-char hard cap. The validator triggers on
# `full_clean()` (used by the admin form), and `clean()` re-checks for
# the case where someone calls .save() directly without validators.

@pytest.mark.django_db
def test_body_html_validator_rejects_oversize_template():
    from django.core.exceptions import ValidationError
    from apps.mailing.models import EMAIL_BODY_MAX_LENGTH

    too_big = "a" * (EMAIL_BODY_MAX_LENGTH + 1)
    t = EmailTemplate(name="big", subject="hi", body_html=too_big, is_active=True)
    with pytest.raises(ValidationError) as exc:
        t.full_clean()
    assert "body_html" in exc.value.message_dict


@pytest.mark.django_db
def test_body_html_at_cap_is_accepted():
    from apps.mailing.models import EMAIL_BODY_MAX_LENGTH
    at_cap = "a" * EMAIL_BODY_MAX_LENGTH
    t = EmailTemplate(name="ok", subject="hi", body_html=at_cap, is_active=True)
    t.full_clean()  # No exception — boundary value is accepted.
    t.save()
    assert EmailTemplate.objects.filter(pk=t.pk).exists()


@pytest.mark.django_db
def test_clean_method_runs_independently_of_validators():
    """If a future change drops `validators=` from the field, `clean()`
    is the second line of defence — admin form save calls full_clean
    which calls clean, and clean alone still rejects oversize input."""
    from django.core.exceptions import ValidationError
    from apps.mailing.models import EMAIL_BODY_MAX_LENGTH

    t = EmailTemplate(
        name="big", subject="hi", body_html="a" * (EMAIL_BODY_MAX_LENGTH + 1)
    )
    with pytest.raises(ValidationError):
        t.clean()
