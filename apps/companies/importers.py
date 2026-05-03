import openpyxl
from django.db import transaction

from .models import Company, Area, Location
from .queries import bust_filter_caches


EXPECTED_HEADERS = {"email", "name"}


def import_companies_from_xlsx(file_obj):
    """
    Parse an .xlsx file and bulk-upsert Company rows.
    Expected columns: name, email, area (optional), location (optional).
    Returns (created, updated, errors) counts.
    """
    wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return 0, 0, ["El archivo está vacío."]

    raw_headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    header_map = {h: i for i, h in enumerate(raw_headers) if h}

    missing = EXPECTED_HEADERS - set(header_map.keys())
    if missing:
        return 0, 0, [f"Columnas requeridas faltantes: {', '.join(missing)}"]

    created = updated = 0
    errors = []

    # Local cache to avoid excessive DB lookups for taxonomy
    area_cache = {}
    location_cache = {}

    for row_num, row in enumerate(rows[1:], start=2):
        def get(col):
            idx = header_map.get(col)
            if idx is None:
                return ""
            val = row[idx]
            return str(val).strip() if val is not None else ""

        email = get("email").lower()
        name = get("name")
        area_name = get("area")
        location_name = get("location")

        if not email or "@" not in email:
            errors.append(f"Fila {row_num}: email inválido '{email}'")
            continue
        if not name:
            errors.append(f"Fila {row_num}: nombre vacío")
            continue

        area_obj = None
        if area_name:
            if area_name not in area_cache:
                area_cache[area_name], _ = Area.objects.get_or_create(name=area_name)
            area_obj = area_cache[area_name]

        location_obj = None
        if location_name:
            if location_name not in location_cache:
                location_cache[location_name], _ = Location.objects.get_or_create(name=location_name)
            location_obj = location_cache[location_name]

        defaults = {
            "name": name,
            "area": area_obj,
            "location": location_obj,
        }
        _, is_new = Company.objects.update_or_create(email=email, defaults=defaults)
        if is_new:
            created += 1
        else:
            updated += 1

    wb.close()
    # Bust once per import on transaction commit rather than once per row via signals.
    transaction.on_commit(bust_filter_caches)
    return created, updated, errors
