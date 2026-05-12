"""
Tests for the .xlsx company importer.

Why this matters: this is the single entry point for hundreds of companies at
a time. A silent bug here = bad data seeding the whole mailing system.
"""
from io import BytesIO
import os
import tempfile
from unittest.mock import patch

import openpyxl
import pytest

from apps.companies import importers
from apps.companies.importers import import_companies_from_xlsx
from apps.companies.models import Blacklist, Company, CompanyImportBatch, Area, Location


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
        ["empresa", "email", "actividad", "provincia"],
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
        ["EMPRESA", "EMAIL", "ACTIVIDAD", "PROVINCIA", "DIRECCION"],
        [
            ["KIKO MILANO", "0383@stores.com", "COSMETICOS: ESTABLECIMIENTOS", "ALICANTE", "HABANERAS"],
        ],
    )
    created, updated, errors, _ = import_companies_from_xlsx(f)
    assert created == 1
    assert errors == []
    c = Company.objects.get(email="0383@stores.com")
    assert c.name == "kiko milano"
    assert c.area.name == "cosmeticos"
    assert c.location.name == "alicante"
    assert c.address == "habaneras"


@pytest.mark.django_db
def test_import_updates_existing_by_email():
    old_area, _ = Area.objects.get_or_create(name="old")
    old_loc, _ = Location.objects.get_or_create(name="old")
    Company.objects.create(email="hr@acme.com", name="old name", area=old_area, location=old_loc)
    f = make_xlsx(
        ["empresa", "email", "actividad", "provincia"],
        [["Acme", "hr@acme.com", "Tech", "Madrid"]],
    )
    created, updated, _, _skip = import_companies_from_xlsx(f)
    assert created == 0
    assert updated == 1
    c = Company.objects.get(email="hr@acme.com")
    assert c.name == "acme"
    assert c.area.name == "tech"
    assert c.location.name == "madrid"


@pytest.mark.django_db
def test_import_uses_provincia_for_location_taxonomy():
    """Verify that the 'provincia' column is used to populate the Location model."""
    f = make_xlsx(
        ["empresa", "email", "provincia", "poblacion"],
        [
            ["Acme Madrid", "madrid@acme.com", "Madrid", "Alcobendas"],
            ["Acme Madrid 2", "madrid2@acme.com", "Madrid", "Torrelodones"],
            ["Acme BCN", "bcn@acme.com", "Barcelona", "Sabadell"],
        ],
    )
    import_companies_from_xlsx(f)
    
    # Both Madrid rows should point to the same Location("madrid")
    madrid_loc = Location.objects.get(name="madrid")
    assert Company.objects.filter(location=madrid_loc).count() == 2
    
    # Barcelona row should point to Location("barcelona")
    bcn_loc = Location.objects.get(name="barcelona")
    assert Company.objects.filter(location=bcn_loc).count() == 1
    
    # The 'poblacion' column data (Alcobendas, etc) should NOT be in the Location table
    assert not Location.objects.filter(name="alcobendas").exists()
    assert not Location.objects.filter(name="torrelodones").exists()
    assert not Location.objects.filter(name="sabadell").exists()


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


@pytest.mark.django_db
def test_chunked_import_processes_all_rows():
    f = make_xlsx(
        ["empresa", "email"],
        [
            ["A", "a@x.com"],
            ["B", "b@x.com"],
            ["C", "c@x.com"],
            ["D", "d@x.com"],
            ["E", "e@x.com"],
        ],
    )
    created, updated, errors, _ = import_companies_from_xlsx(f, chunk_size=2)
    assert created == 5
    assert updated == 0
    assert errors == []
    assert Company.objects.count() == 5


@pytest.mark.django_db
def test_chunked_import_writes_progress_after_each_chunk():
    """Each chunk commit MUST write cumulative progress to the batch row.

    We capture every _write_progress call so we can assert the importer
    advances counters at chunk boundaries (not just at the end).
    """
    batch = CompanyImportBatch.objects.create(status="PROCESSING")
    f = make_xlsx(
        ["empresa", "email"],
        [
            ["A", "a@x.com"],
            ["B", "b@x.com"],
            ["C", "c@x.com"],
            ["D", "d@x.com"],
            ["E", "e@x.com"],
        ],
    )

    snapshots = []
    real = importers._write_progress

    def spy(_batch, processed_rows, created, updated, blacklisted_skipped, errors):
        snapshots.append((processed_rows, created, updated))
        real(_batch, processed_rows, created, updated, blacklisted_skipped, errors)

    with patch.object(importers, "_write_progress", side_effect=spy):
        import_companies_from_xlsx(f, batch=batch, chunk_size=2)

    # 5 rows / chunk_size=2 = chunks of [2, 2, 1] = 3 progress writes.
    assert [s[0] for s in snapshots] == [2, 4, 5]
    batch.refresh_from_db()
    assert batch.processed_rows == 5
    assert batch.created_count == 5


@pytest.mark.django_db
def test_chunked_import_is_idempotent_on_partial_rerun():
    """Inject a failure mid-chunk, observe partial state, then re-run cleanly
    and assert the final state matches a fresh import."""
    rows = [["Co" + str(i), f"co{i}@x.com"] for i in range(6)]
    f = make_xlsx(["empresa", "email"], rows)

    batch = CompanyImportBatch.objects.create(status="PROCESSING")

    call_count = {"n": 0}
    real = importers._write_progress

    def fail_on_third_chunk(b, processed, c, u, bk, e):
        call_count["n"] += 1
        real(b, processed, c, u, bk, e)
        if call_count["n"] == 2:
            raise RuntimeError("simulated mid-import failure")

    with patch.object(importers, "_write_progress", side_effect=fail_on_third_chunk):
        with pytest.raises(RuntimeError):
            import_companies_from_xlsx(f, batch=batch, chunk_size=2)

    partial_count = Company.objects.count()
    assert 0 < partial_count < 6  # mid-import: some rows committed, not all

    # Re-run on the same file, no patch — must converge.
    created2, updated2, errors2, _ = import_companies_from_xlsx(f, chunk_size=2)
    assert errors2 == []
    assert Company.objects.count() == 6
    # Row identity is the unique email, so re-running cannot duplicate.
    assert (
        Company.objects.filter(email__in=[r[1] for r in rows]).count() == 6
    )


@pytest.mark.django_db
def test_chunk_does_not_abort_on_single_bad_row():
    f = make_xlsx(
        ["empresa", "email"],
        [
            ["Good A", "a@x.com"],
            ["Bad", "not-an-email"],
            ["Good B", "b@x.com"],
        ],
    )
    created, updated, errors, _ = import_companies_from_xlsx(f, chunk_size=10)
    assert created == 2
    assert len(errors) == 1
    assert Company.objects.filter(email="a@x.com").exists()
    assert Company.objects.filter(email="b@x.com").exists()


@pytest.mark.django_db
def test_trailing_blank_rows_do_not_inflate_processed_rows():
    batch = CompanyImportBatch.objects.create(status="PROCESSING")
    f = make_xlsx(
        ["empresa", "email"],
        [
            ["A", "a@x.com"],
            ["B", "b@x.com"],
            [None, None],
            [None, None],
            ["", ""],
        ],
    )
    import_companies_from_xlsx(f, batch=batch, chunk_size=10)
    batch.refresh_from_db()
    assert batch.processed_rows == 2
    assert batch.created_count == 2
