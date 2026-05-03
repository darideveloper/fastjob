# Change: Update Company Import Format and Data Normalization

## Why
The current company importer supports only 4 fields and lacks strict casing enforcement. The new business requirement demands capturing 11 fields from a specific Spanish Excel format (EMPRESA, ACTIVIDAD, etc.) and ensuring all searchable data is stored in lowercase to prevent duplicates and improve filter consistency.

## What Changes
- **MODIFIED**: `Company` model expanded with 7 new fields (address, zip_code, province, community, phone, fax, website).
- **MODIFIED**: Importer logic updated to map Spanish headers and split the `ACTIVIDAD` field.
- **MODIFIED**: Strict lowercase normalization enforced for Company, Area, and Location names.
- **ADDED**: Data migration to lowercase existing records.

## Impact
- Affected specs: `companies`
- Affected code: `apps/companies/models.py`, `apps/companies/importers.py`, `apps/companies/admin.py`, `apps/companies/tests/`
