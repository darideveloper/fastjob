"""Tests for apps.companies.queries — the shared query helper and cache layer."""
import pytest
from django.core.cache import cache

from apps.companies.models import Company
from apps.companies.queries import (
    bust_filter_caches,
    get_company_count,
    get_filter_options,
    matching_companies_qs,
)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# matching_companies_qs
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_matching_qs_no_filters_returns_all():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="Madrid")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="Barcelona")
    assert matching_companies_qs().count() == 2


@pytest.mark.django_db
def test_matching_qs_exact_area_excludes_substring():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    Company.objects.create(email="b@x.com", name="B", area="Tecnología Industrial", location="")
    qs = matching_companies_qs(area="Tecnología")
    assert qs.count() == 1
    assert qs.first().email == "a@x.com"


@pytest.mark.django_db
def test_matching_qs_case_insensitive():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    qs = matching_companies_qs(area="tecnología")
    assert qs.count() == 1


@pytest.mark.django_db
def test_matching_qs_location_filter():
    Company.objects.create(email="a@x.com", name="A", area="", location="Madrid")
    Company.objects.create(email="b@x.com", name="B", area="", location="Barcelona")
    qs = matching_companies_qs(location="Madrid")
    assert qs.count() == 1
    assert qs.first().email == "a@x.com"


@pytest.mark.django_db
def test_matching_qs_none_values_mean_no_filter():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="Madrid")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="Barcelona")
    assert matching_companies_qs(area=None, location=None).count() == 2


# ---------------------------------------------------------------------------
# get_filter_options
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_filter_options_excludes_blanks():
    Company.objects.create(email="a@x.com", name="A", area="", location="")
    Company.objects.create(email="b@x.com", name="B", area="Tecnología", location="Madrid")
    opts = get_filter_options()
    assert "" not in opts["areas"]
    assert "" not in opts["locations"]


@pytest.mark.django_db
def test_filter_options_deduplicates_case_insensitively():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    Company.objects.create(email="b@x.com", name="B", area="tecnología", location="")
    opts = get_filter_options()
    assert len(opts["areas"]) == 1


@pytest.mark.django_db
def test_filter_options_sorted_alphabetically():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="")
    Company.objects.create(email="c@x.com", name="C", area="Marketing", location="")
    opts = get_filter_options()
    assert opts["areas"] == sorted(opts["areas"], key=str.lower)


@pytest.mark.django_db
def test_filter_options_cached_avoids_repeat_queries(django_assert_num_queries):
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    get_filter_options()
    with django_assert_num_queries(0):
        opts = get_filter_options()
    assert "Tecnología" in opts["areas"]


# ---------------------------------------------------------------------------
# get_company_count
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_get_company_count_no_filters():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="Madrid")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="Barcelona")
    assert get_company_count() == 2


@pytest.mark.django_db
def test_get_company_count_with_filter():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="")
    assert get_company_count(area="Tecnología") == 1


# ---------------------------------------------------------------------------
# bust_filter_caches
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_bust_invalidates_options_cache():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    get_filter_options()

    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="")
    bust_filter_caches()

    opts = get_filter_options()
    assert "Diseño" in opts["areas"]


@pytest.mark.django_db
def test_bust_on_company_save():
    Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    get_filter_options()

    Company.objects.create(email="b@x.com", name="B", area="Diseño", location="")

    opts = get_filter_options()
    assert "Diseño" in opts["areas"]


@pytest.mark.django_db
def test_bust_on_company_delete():
    c = Company.objects.create(email="a@x.com", name="A", area="Tecnología", location="")
    get_filter_options()

    c.delete()

    opts = get_filter_options()
    assert "Tecnología" not in opts["areas"]
