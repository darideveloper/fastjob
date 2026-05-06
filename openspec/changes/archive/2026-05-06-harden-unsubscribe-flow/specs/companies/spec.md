# companies spec deltas — harden-unsubscribe-flow

## ADDED Requirements

### Requirement: Blacklist Write Normalization

All writes to the `Blacklist` table MUST go through a single helper, `Blacklist.add(email, reason="unsubscribe")`. The helper MUST lowercase and strip the email before performing `get_or_create`, so that the lookup phase of `get_or_create` is consistent with the lowercased value the `LowercaseFieldsMixin` writes on `save()`. The helper MUST raise `ValueError` on empty input.

#### Scenario: Mixed-case email normalized on insert

- **WHEN** `Blacklist.add("Foo@Empresa.ES")` is called for the first time
- **THEN** exactly one row is created with `email == "foo@empresa.es"` and `reason == "unsubscribe"`

#### Scenario: Repeat call is idempotent

- **GIVEN** a `Blacklist` row already exists for `"foo@empresa.es"`
- **WHEN** `Blacklist.add("FOO@empresa.es")` is called
- **THEN** no new row is created
- **AND** no `IntegrityError` is raised

#### Scenario: Empty email raises

- **WHEN** `Blacklist.add("")` or `Blacklist.add(None)` is called
- **THEN** the helper raises `ValueError`
- **AND** no row is created

## MODIFIED Requirements

### Requirement: Enhanced Spanish XLSX Importer
The system SHALL support importing companies from an Excel file using Spanish headers and specific business logic for Spanish data.
The importer MUST process rows within a background task context and:
1. Map `EMPRESA` to `name`, `ACTIVIDAD` to `area`, `DIRECCION` to `address`, `CP` to `zip_code`, `POBLACION` to `location`, `PROVINCIA` to `province`, `COMUNIDAD` to `community`, `TELEFONO` to `phone`, `FAX` to `fax`, `EMAIL` to `email`, and `WEBSITE` to `website`.
2. Split the `ACTIVIDAD` field by the first colon (`:`) and use only the first part as the `Area` name.
3. Normalize all imported string data to lowercase.
4. Materialise the current `Blacklist` email set once per import call and track a `blacklisted_skipped` counter that records the number of **distinct** blacklisted emails encountered in the file — not raw rows. If the same blacklisted email appears N times in the file (e.g. dirty exports with duplicates), the counter MUST advance by exactly 1 across those N rows. The `Company` row MUST still be upserted for every row (so that the row exists if the email is later removed from the blacklist), and the count MUST be returned alongside `created` / `updated` / `errors` and persisted on the `CompanyImportBatch` row that drives the import.

#### Scenario: Importer splits ACTIVIDAD and lowercases data
- **GIVEN** an Excel row with `EMPRESA = "KIKO MILANO"`, `ACTIVIDAD = "COSMETICOS: ESTABLECIMIENTOS"`, and `POBLACION = "TORREVIEJA"`
- **WHEN** the file is imported
- **THEN** a `Company` is created with name `"kiko milano"`
- **AND** it is linked to an `Area` named `"cosmeticos"`
- **AND** it is linked to a `Location` named `"torrevieja"`.

#### Scenario: Importer counts blacklisted rows without dropping them

- **GIVEN** a `Blacklist` row exists for `"contact@kiko.es"`
- **AND** the import file contains a row with `EMAIL = "Contact@kiko.es"`
- **WHEN** the import runs
- **THEN** the returned `blacklisted_skipped` is `1`
- **AND** the `Company` row for `"contact@kiko.es"` is still created or updated
- **AND** the `CompanyImportBatch` record persists `blacklisted_skipped = 1`

#### Scenario: Duplicate blacklisted email in the input is counted once

- **GIVEN** a `Blacklist` row exists for `"contact@kiko.es"`
- **AND** the import file contains three rows whose `EMAIL` column lowercases to `"contact@kiko.es"` (e.g. `"contact@kiko.es"`, `"Contact@KIKO.es"`, `"  contact@kiko.es  "`)
- **WHEN** the import runs
- **THEN** the returned `blacklisted_skipped` is `1`, not `3`
- **AND** exactly one `Company` row exists for `"contact@kiko.es"` (the upsert collapses duplicates by unique email)
- **AND** the `CompanyImportBatch` record persists `blacklisted_skipped = 1`

#### Scenario: Admin sees the blacklisted-skipped count after import
- **GIVEN** an `CompanyImportBatch` with `blacklisted_skipped = 5`
- **WHEN** an administrator opens the batch's admin detail page
- **THEN** the displayed batch summary includes `blacklisted_skipped = 5`
