import pytest
from apps.companies.models import Blacklist


@pytest.mark.django_db
def test_blacklist_add_creates_lowercase_row():
    obj, created = Blacklist.add("Foo@Bar.com")
    assert created is True
    assert obj.email == "foo@bar.com"
    assert Blacklist.objects.count() == 1


@pytest.mark.django_db
def test_blacklist_add_is_idempotent():
    obj1, created1 = Blacklist.add("Test@Example.COM")
    obj2, created2 = Blacklist.add("test@example.com")
    assert created1 is True
    assert created2 is False
    assert obj1.pk == obj2.pk
    assert Blacklist.objects.count() == 1


@pytest.mark.django_db
def test_blacklist_add_raises_on_empty_email():
    with pytest.raises(ValueError, match="empty email"):
        Blacklist.add("")


@pytest.mark.django_db
def test_blacklist_add_raises_on_whitespace_email():
    with pytest.raises(ValueError, match="empty email"):
        Blacklist.add("   ")


@pytest.mark.django_db
def test_blacklist_add_strips_whitespace():
    obj, created = Blacklist.add("  user@example.com  ")
    assert obj.email == "user@example.com"
