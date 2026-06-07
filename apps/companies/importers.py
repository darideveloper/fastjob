import openpyxl
from django.db import transaction

from .models import Blacklist, Company, Area, Location, SubArea


EXPECTED_HEADERS = {"email", "empresa"}

# Fields written by bulk_update for an existing Company. `email` is the row
# identity (unique key) and `created_at` is auto_now_add — both are excluded
# on purpose.
COMPANY_UPDATE_FIELDS = [
    "name",
    "area",
    "sub_area",
    "location",
    "address",
    "zip_code",
    "province",
    "community",
    "phone",
    "fax",
    "website",
]


def _row_is_blank(row):
    """A row is blank when every cell is None or an all-whitespace string."""
    for value in row:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return False
    return True


def _parse_row(row, header_map, row_num):
    """Parse and normalize a single sheet row.

    Returns (parsed_dict, error). On a per-row data error, parsed_dict is None.
    Lowercasing is performed here because bulk_create / bulk_update bypass
    Model.save() and therefore bypass LowercaseFieldsMixin.
    """

    def get(col):
        idx = header_map.get(col)
        if idx is None or idx >= len(row):
            return ""
        val = row[idx]
        return str(val).strip() if val is not None else ""

    email = get("email").lower()
    name = get("empresa").lower()[:300]

    raw_actividad = get("actividad")
    area_name = raw_actividad.split(":")[0].strip().lower()[:200] if raw_actividad else ""

    sub_area_name = get("sub actividad").lower()[:200]

    location_name = get("provincia").lower()[:200]
    address = get("direccion").lower()[:500]
    zip_code = get("cp")[:20]
    province = get("provincia").lower()[:100]
    community = get("comunidad").lower()[:100]
    phone = get("telefono")[:50]
    fax = get("fax")[:50]
    website = get("website").lower()[:500]

    if not email or "@" not in email:
        return None, f"Fila {row_num}: email inválido '{email}'"
    if not name:
        return None, f"Fila {row_num}: nombre vacío"

    return (
        {
            "email": email,
            "name": name,
            "area_name": area_name,
            "sub_area_name": sub_area_name,
            "location_name": location_name,
            "address": address,
            "zip_code": zip_code,
            "province": province,
            "community": community,
            "phone": phone,
            "fax": fax,
            "website": website,
        },
        None,
    )


def _resolve_taxonomy(model, names, cache):
    """Ensure every name in `names` has a row in `model`, using `cache` as a
    local memoization to avoid re-querying within a single import run."""
    missing_in_cache = {n for n in names if n and n not in cache}
    if not missing_in_cache:
        return

    existing = model.objects.filter(name__in=missing_in_cache)
    for obj in existing:
        cache[obj.name] = obj

    still_missing = missing_in_cache - set(cache.keys())
    if still_missing:
        # Names are already lowercased by _parse_row; bulk_create bypasses
        # LowercaseFieldsMixin.save() so the casing must be set upstream.
        model.objects.bulk_create(
            [model(name=n) for n in still_missing], ignore_conflicts=True
        )
        for obj in model.objects.filter(name__in=still_missing):
            cache[obj.name] = obj


def _process_chunk(parsed_rows, blacklisted_set, seen_blacklisted, area_cache, location_cache, sub_area_cache):
    """Run one chunk: resolve taxonomy in bulk, partition by existing email,
    bulk_create new rows, bulk_update existing rows. Returns
    (created_delta, updated_delta, blacklisted_delta).
    """
    if not parsed_rows:
        return 0, 0, 0

    distinct_areas = {r["area_name"] for r in parsed_rows if r["area_name"]}
    distinct_locations = {r["location_name"] for r in parsed_rows if r["location_name"]}
    distinct_sub_areas = {r["sub_area_name"] for r in parsed_rows if r["sub_area_name"]}
    _resolve_taxonomy(Area, distinct_areas, area_cache)
    _resolve_taxonomy(Location, distinct_locations, location_cache)
    _resolve_taxonomy(SubArea, distinct_sub_areas, sub_area_cache)

    chunk_emails = [r["email"] for r in parsed_rows]
    existing_map = dict(
        Company.objects.filter(email__in=chunk_emails).values_list("email", "id")
    )

    blacklisted_delta = 0
    created_delta = 0
    updated_delta = 0
    new_emails_in_chunk = set()
    last_by_email = {}

    # Pass 1: per-row accounting (preserves the semantic of the prior
    # per-row update_or_create — each input row contributes 1 to
    # created or updated, even if the same email repeats within the chunk).
    for r in parsed_rows:
        email = r["email"]
        last_by_email[email] = r
        if email in blacklisted_set and email not in seen_blacklisted:
            blacklisted_delta += 1
            seen_blacklisted.add(email)

        if email in existing_map:
            updated_delta += 1
        elif email in new_emails_in_chunk:
            updated_delta += 1
        else:
            created_delta += 1
            new_emails_in_chunk.add(email)

    # Pass 2: build dedup'd payloads for the bulk operations. Last write wins
    # both for duplicate emails within the chunk and against existing DB rows.
    new_rows = []
    update_rows = []
    for email, r in last_by_email.items():
        company_kwargs = {
            "email": email,
            "name": r["name"],
            "area": area_cache.get(r["area_name"]) if r["area_name"] else None,
            "sub_area": sub_area_cache.get(r["sub_area_name"]) if r["sub_area_name"] else None,
            "location": location_cache.get(r["location_name"]) if r["location_name"] else None,
            "address": r["address"],
            "zip_code": r["zip_code"],
            "province": r["province"],
            "community": r["community"],
            "phone": r["phone"],
            "fax": r["fax"],
            "website": r["website"],
        }
        if email in existing_map:
            obj = Company(**company_kwargs)
            obj.id = existing_map[email]
            update_rows.append(obj)
        else:
            new_rows.append(Company(**company_kwargs))

    if new_rows:
        Company.objects.bulk_create(new_rows, ignore_conflicts=True)
    if update_rows:
        Company.objects.bulk_update(update_rows, fields=COMPANY_UPDATE_FIELDS)

    return created_delta, updated_delta, blacklisted_delta


def _write_progress(batch, processed_rows, created, updated, blacklisted_skipped, errors):
    batch.processed_rows = processed_rows
    batch.created_count = created
    batch.updated_count = updated
    batch.blacklisted_skipped = blacklisted_skipped
    batch.error_log = list(errors)
    batch.save(
        update_fields=[
            "processed_rows",
            "created_count",
            "updated_count",
            "blacklisted_skipped",
            "error_log",
            "updated_at",
        ]
    )


def import_companies_from_xlsx(file_path, batch=None, chunk_size=1000):
    """
    Parse an .xlsx file and bulk-upsert Company rows in chunks.

    Each chunk of `chunk_size` non-blank rows is processed inside its own
    `transaction.atomic()` block, so its writes (and the cumulative counter
    updates on `batch`, when provided) become visible to other DB connections
    chunk-by-chunk — notably to the admin progress endpoint, which reads from
    a separate connection from the celery worker.

    Returns (created, updated, errors, blacklisted_skipped) counts.
    """
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    try:
        first_row = next(rows_iter)
    except StopIteration:
        wb.close()
        return 0, 0, ["El archivo está vacío."], 0

    raw_headers = [str(h).strip().lower() if h else "" for h in first_row]
    header_map = {h: i for i, h in enumerate(raw_headers) if h}

    missing = EXPECTED_HEADERS - set(header_map.keys())
    if missing:
        wb.close()
        return 0, 0, [f"Columnas requeridas faltantes: {', '.join(missing)}"], 0

    blacklisted_set = set(Blacklist.objects.values_list("email", flat=True))
    seen_blacklisted = set()
    area_cache = {}
    location_cache = {}
    sub_area_cache = {}

    created_total = 0
    updated_total = 0
    blacklisted_total = 0
    processed_total = 0
    errors = []

    chunk_buffer = []
    chunk_row_nums = []

    def flush():
        nonlocal created_total, updated_total, blacklisted_total, processed_total
        if not chunk_buffer:
            return

        # Pre-validate every row BEFORE building the bulk-write partition.
        # bulk_create(ignore_conflicts=True) only suppresses unique-key
        # conflicts, NOT generic integrity errors, so a malformed row reaching
        # bulk_create would roll the entire chunk back.
        valid_rows = []
        for raw_row, row_num in zip(chunk_buffer, chunk_row_nums):
            parsed, err = _parse_row(raw_row, header_map, row_num)
            if err is not None:
                errors.append(err)
            else:
                valid_rows.append(parsed)

        with transaction.atomic():
            c, u, b = _process_chunk(
                valid_rows,
                blacklisted_set,
                seen_blacklisted,
                area_cache,
                location_cache,
                sub_area_cache,
            )

        created_total += c
        updated_total += u
        blacklisted_total += b
        processed_total += len(chunk_buffer)

        chunk_buffer.clear()
        chunk_row_nums.clear()

        if batch is not None:
            _write_progress(
                batch,
                processed_total,
                created_total,
                updated_total,
                blacklisted_total,
                errors,
            )

    for row_num, row in enumerate(rows_iter, start=2):
        if _row_is_blank(row):
            continue
        chunk_buffer.append(row)
        chunk_row_nums.append(row_num)
        if len(chunk_buffer) >= chunk_size:
            flush()

    flush()

    wb.close()
    return created_total, updated_total, errors, blacklisted_total
