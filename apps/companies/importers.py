import openpyxl
from django.db import transaction

from .models import Blacklist, Company, Area, Location
from .queries import bust_filter_caches


EXPECTED_HEADERS = {"email", "empresa"}


def import_companies_from_xlsx(file_path):
    """
    Parse an .xlsx file and bulk-upsert Company rows.
    Expected columns (Spanish): empresa, email, actividad, direccion, cp, poblacion,
    provincia, comunidad, telefono, fax, website.
    Returns (created, updated, errors, blacklisted_skipped) counts.
    """
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    try:
        first_row = next(rows_iter)
    except StopIteration:
        return 0, 0, ["El archivo está vacío."], 0

    raw_headers = [str(h).strip().lower() if h else "" for h in first_row]
    header_map = {h: i for i, h in enumerate(raw_headers) if h}

    missing = EXPECTED_HEADERS - set(header_map.keys())
    if missing:
        return 0, 0, [f"Columnas requeridas faltantes: {', '.join(missing)}"], 0

    created = updated = 0
    blacklisted_skipped = 0
    errors = []

    blacklisted_set = set(Blacklist.objects.values_list("email", flat=True))
    # Track distinct blacklisted emails actually seen in this file so duplicates
    # in dirty exports do not inflate the operator-visible counter.
    seen_blacklisted = set()

    # Local cache to avoid excessive DB lookups for taxonomy
    area_cache = {}
    location_cache = {}

    with transaction.atomic():
        for row_num, row in enumerate(rows_iter, start=2):
            def get(col):
                idx = header_map.get(col)
                if idx is None or idx >= len(row):
                    return ""
                val = row[idx]
                return str(val).strip() if val is not None else ""

            email = get("email").lower()
            name = get("empresa").lower()
            
            # Split actividad by ':' and take first part (e.g. "ROPA DIVERSA: ESTABLECIMIENTOS" -> "ROPA DIVERSA")
            raw_actividad = get("actividad")
            area_name = raw_actividad.split(":")[0].strip().lower() if raw_actividad else ""
            
            location_name = get("poblacion").lower()[:200]
            address = get("direccion").lower()[:500]
            zip_code = get("cp")[:20]
            province = get("provincia").lower()[:100]
            community = get("comunidad").lower()[:100]
            phone = get("telefono")[:50]
            fax = get("fax")[:50]
            website = get("website").lower()[:500]

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
                "address": address,
                "zip_code": zip_code,
                "province": province,
                "community": community,
                "phone": phone,
                "fax": fax,
                "website": website,
            }
            if email in blacklisted_set and email not in seen_blacklisted:
                blacklisted_skipped += 1
                seen_blacklisted.add(email)

            _, is_new = Company.objects.update_or_create(email=email, defaults=defaults)
            if is_new:
                created += 1
            else:
                updated += 1

    wb.close()
    # Bust once per import on transaction commit rather than once per row via signals.
    transaction.on_commit(bust_filter_caches)
    return created, updated, errors, blacklisted_skipped
