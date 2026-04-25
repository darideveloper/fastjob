import openpyxl
from .models import Company


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

    for row_num, row in enumerate(rows[1:], start=2):
        def get(col):
            idx = header_map.get(col)
            if idx is None:
                return ""
            val = row[idx]
            return str(val).strip() if val is not None else ""

        email = get("email").lower()
        name = get("name")

        if not email or "@" not in email:
            errors.append(f"Fila {row_num}: email inválido '{email}'")
            continue
        if not name:
            errors.append(f"Fila {row_num}: nombre vacío")
            continue

        defaults = {
            "name": name,
            "area": get("area"),
            "location": get("location"),
        }
        _, is_new = Company.objects.update_or_create(email=email, defaults=defaults)
        if is_new:
            created += 1
        else:
            updated += 1

    wb.close()
    return created, updated, errors
