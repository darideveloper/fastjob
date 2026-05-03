# Design: Company Import Format and Data Normalization

## Data Model Changes
The `Company` model will be expanded with the following fields:
- `address` (CharField, max_length=500, blank=True)
- `zip_code` (CharField, max_length=20, blank=True)
- `province` (CharField, max_length=100, blank=True)
- `community` (CharField, max_length=100, blank=True)
- `phone` (CharField, max_length=50, blank=True)
- `fax` (CharField, max_length=50, blank=True)
- `website` (URLField, max_length=500, blank=True) - *Note: Excel data might not be valid URLs, maybe CharField is safer if we want to preserve exactly what's in Excel.*

Given the user requirement "all data in database, should be in lowercase", we will implement:
1.  **Normalization at the model level**: Override `save()` or use signals to lowercase fields that are used for filtering or searching (`name`, `email`, `address`, etc.).
2.  **Normalization at the importer level**: The `import_companies_from_xlsx` function will lowercase all values before creating/updating objects.

## Importer Mapping
The new Excel format maps to the model fields as follows:

| Excel Header | Company Model Field | Processing |
| :--- | :--- | :--- |
| `EMPRESA` | `name` | Lowercase |
| `ACTIVIDAD` | `area` (ForeignKey) | Split by `:`, take first part, lowercase |
| `DIRECCION` | `address` | Lowercase |
| `CP` | `zip_code` | |
| `POBLACION` | `location` (ForeignKey) | Lowercase |
| `PROVINCIA` | `province` | Lowercase |
| `COMUNIDAD` | `community` | Lowercase |
| `TELEFONO` | `phone` | |
| `FAX` | `fax` | |
| `EMAIL` | `email` | Lowercase |
| `WEBSITE` | `website` | Lowercase |

## Normalization Strategy
To ensure consistency across the application:
- `Area.name` and `Location.name` will always be stored in lowercase.
- The `Area.objects.get_or_create` and `Location.objects.get_or_create` calls in the importer will use lowercased names.
- Existing records will be updated via a one-time data migration.

## Trade-offs
- **URLField vs CharField**: The `WEBSITE` column might contain invalid URL formats (e.g. missing `https://`). `URLField` would reject these. We will use `CharField` for `website` to ensure all data from the spreadsheet is captured, even if not perfectly formatted as a URL.
- **Model vs Importer Normalization**: Applying normalization in `save()` ensures consistency even if rows are added via the admin or other scripts. However, it can be surprising for developers. We will prioritize normalization in the importer and add model-level `clean()` or `save()` logic for critical fields.
