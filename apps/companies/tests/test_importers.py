"""
Tests for the .xlsx company importer.

Why this matters: this is the single entry point for hundreds of companies at
a time. A silent bug here = bad data seeding the whole mailing system.
"""
from io import BytesIO
import os
import tempfile

import openpyxl
import pytest

from apps.companies.importers import import_companies_from_xlsx
from apps.companies.models import Blacklist, Company


def make_xlsx(headers, rows):
    """Build a temporary .xlsx file on disk for the importer to consume."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    wb.save(path)
    return path


@pytest.mark.django_db
def test_import_creates_new_companies():
    f = make_xlsx(
        ["empresa", "email", "actividad", "poblacion"],
        [
            ["Acme", "hr@acme.com", "Tech", "Madrid"],
            ["Beta", "jobs@beta.io", "Design", "Barcelona"],
        ],
    )
    created, updated, errors, blacklisted_skipped = import_companies_from_xlsx(f)
    assert created == 2
    assert updated == 0
    assert errors == []
    assert blacklisted_skipped == 0
    assert Company.objects.count() == 2
    assert Company.objects.get(email="hr@acme.com").name == "acme"


@pytest.mark.django_db
def test_import_with_spanish_headers_and_splitting():
    f = make_xlsx(
        ["EMPRESA", "EMAIL", "ACTIVIDAD", "POBLACION", "DIRECCION"],
        [
            ["KIKO MILANO", "0383@stores.com", "COSMETICOS: ESTABLECIMIENTOS", "TORREVIEJA", "HABANERAS"],
        ],
    )
    created, updated, errors, _ = import_companies_from_xlsx(f)
    assert created == 1
    assert errors == []
    c = Company.objects.get(email="0383@stores.com")
    assert c.name == "kiko milano"
    assert c.area.name == "cosmeticos"
    assert c.location.name == "torrevieja"
    assert c.address == "habaneras"


@pytest.mark.django_db
def test_import_updates_existing_by_email():
    from apps.companies.models import Area, Location
    old_area, _ = Area.objects.get_or_create(name="old")
    old_loc, _ = Location.objects.get_or_create(name="old")
    Company.objects.create(email="hr@acme.com", name="old name", area=old_area, location=old_loc)
    f = make_xlsx(
        ["empresa", "email", "actividad", "poblacion"],
        [["Acme", "hr@acme.com", "Tech", "Madrid"]],
    )
    created, updated, _, _skip = import_companies_from_xlsx(f)
    assert created == 0
    assert updated == 1
    c = Company.objects.get(email="hr@acme.com")
    assert c.name == "acme"
    assert c.area.name == "tech"


@pytest.mark.django_db
def test_import_skips_rows_with_bad_email():
    f = make_xlsx(
        ["empresa", "email"],
        [
            ["Good Co", "hr@good.com"],
            ["Bad Co", "not-an-email"],
            ["No Email", ""],
        ],
    )
    created, _, errors, _skip = import_companies_from_xlsx(f)
    assert created == 1
    assert len(errors) == 2  # one for "not-an-email", one for empty


@pytest.mark.django_db
def test_import_fails_gracefully_without_required_headers():
    f = make_xlsx(["empresa"], [["Only Name"]])  # missing email column
    created, updated, errors, _skip = import_companies_from_xlsx(f)
    assert created == 0
    assert updated == 0
    assert errors  # should report the missing column


@pytest.mark.django_db
def test_import_handles_empty_file():
    wb = openpyxl.Workbook()
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    wb.save(path)
    created, updated, errors, _skip = import_companies_from_xlsx(path)
    assert created == 0
    assert updated == 0
    os.remove(path)


@pytest.mark.django_db
def test_import_is_case_insensitive_for_email():
    f = make_xlsx(
        ["empresa", "email"],
        [["Acme", "HR@ACME.COM"]],
    )
    import_companies_from_xlsx(f)
    assert Company.objects.filter(email="hr@acme.com").exists()


@pytest.mark.django_db
def test_importer_counts_blacklisted_rows():
    """Verifies the distinct-blacklisted-email count: each unique blacklisted
    address in the file contributes 1 to the counter, and blacklisted Company
    rows are still upserted so a future blacklist removal doesn't lose data.
    """
    Blacklist.objects.create(email="blacklisted@acme.com")
    Blacklist.objects.create(email="also@blocked.com")

    f = make_xlsx(
        ["empresa", "email"],
        [
            ["Acme", "blacklisted@acme.com"],
            ["Blocked", "also@blocked.com"],
            ["Normal", "normal@company.com"],
        ],
    )
    created, updated, errors, blacklisted_skipped = import_companies_from_xlsx(f)

    assert blacklisted_skipped == 2
    assert created == 3  # all rows are still written to Company
    assert errors == []
    assert Company.objects.filter(email="blacklisted@acme.com").exists()
    assert Company.objects.filter(email="also@blocked.com").exists()


@pytest.mark.django_db
def test_importer_counts_distinct_blacklisted_emails():
    """Duplicate blacklisted emails in the input must count as ONE skip.

    Dirty exports often repeat the same address with mixed casing or stray
    whitespace. The counter tracks distinct emails, not raw rows — otherwise
    operators see inflated numbers that don't reconcile against
    `Company.objects.filter(email__in=Blacklist...).count()`.
    """
    Blacklist.objects.create(email="contact@kiko.es")

    f = make_xlsx(
        ["empresa", "email"],
        [
            ["Kiko Store 1", "contact@kiko.es"],
            ["Kiko Store 2", "Contact@KIKO.es"],
            ["Kiko Store 3", "  contact@kiko.es  "],
        ],
    )
    created, updated, errors, blacklisted_skipped = import_companies_from_xlsx(f)

    assert blacklisted_skipped == 1
    # The unique constraint on Company.email collapses the three rows into
    # one upsert — first row creates, the next two update.
    assert Company.objects.filter(email="contact@kiko.es").count() == 1
    assert created + updated == 3
    assert errors == []
