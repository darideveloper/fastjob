"""
Tests for the .xlsx company importer.

Why this matters: this is the single entry point for hundreds of companies at
a time. A silent bug here = bad data seeding the whole mailing system.
"""
from io import BytesIO

import openpyxl
import pytest

from apps.companies.importers import import_companies_from_xlsx
from apps.companies.models import Company


def make_xlsx(headers, rows):
    """Build an in-memory .xlsx for the importer to consume."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@pytest.mark.django_db
def test_import_creates_new_companies():
    f = make_xlsx(
        ["name", "email", "area", "location"],
        [
            ["Acme", "hr@acme.com", "Tech", "Madrid"],
            ["Beta", "jobs@beta.io", "Design", "Barcelona"],
        ],
    )
    created, updated, errors = import_companies_from_xlsx(f)
    assert created == 2
    assert updated == 0
    assert errors == []
    assert Company.objects.count() == 2


@pytest.mark.django_db
def test_import_updates_existing_by_email():
    Company.objects.create(email="hr@acme.com", name="Old Name", area="Old", location="Old")
    f = make_xlsx(
        ["name", "email", "area", "location"],
        [["Acme", "hr@acme.com", "Tech", "Madrid"]],
    )
    created, updated, _ = import_companies_from_xlsx(f)
    assert created == 0
    assert updated == 1
    c = Company.objects.get(email="hr@acme.com")
    assert c.name == "Acme"
    assert c.area == "Tech"


@pytest.mark.django_db
def test_import_skips_rows_with_bad_email():
    f = make_xlsx(
        ["name", "email"],
        [
            ["Good Co", "hr@good.com"],
            ["Bad Co", "not-an-email"],
            ["No Email", ""],
        ],
    )
    created, _, errors = import_companies_from_xlsx(f)
    assert created == 1
    assert len(errors) == 2  # one for "not-an-email", one for empty


@pytest.mark.django_db
def test_import_fails_gracefully_without_required_headers():
    f = make_xlsx(["name"], [["Only Name"]])  # missing email column
    created, updated, errors = import_companies_from_xlsx(f)
    assert created == 0
    assert updated == 0
    assert errors  # should report the missing column


@pytest.mark.django_db
def test_import_handles_empty_file():
    wb = openpyxl.Workbook()
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    created, updated, errors = import_companies_from_xlsx(buf)
    # Either zero-creation with error or explicit "empty" signal — both are OK.
    assert created == 0
    assert updated == 0


@pytest.mark.django_db
def test_import_is_case_insensitive_for_email():
    f = make_xlsx(
        ["name", "email"],
        [["Acme", "HR@ACME.COM"]],
    )
    import_companies_from_xlsx(f)
    assert Company.objects.filter(email="hr@acme.com").exists()
