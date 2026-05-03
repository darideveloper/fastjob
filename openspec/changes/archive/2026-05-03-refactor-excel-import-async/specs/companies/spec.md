## ADDED Requirements
### Requirement: Asynchronous Excel Import Processing
The system SHALL process Excel company imports asynchronously to prevent request timeouts.
- The system MUST define a `CompanyImportBatch` model (or similar) to store the uploaded file and track processing status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- The admin view for importing Excel files MUST accept the file, create a tracking record, enqueue a background task, and redirect the user immediately with a success message indicating the background process has started.
- The background task MUST update the status of the tracking record as it progresses and record the final counts of created/updated records or any errors encountered.

#### Scenario: Admin uploads a large Excel file
- **WHEN** an administrator uploads a valid `.xlsx` file via the import view
- **THEN** the system immediately redirects to the change list with a message "Import started in the background"
- **AND** the system creates a `CompanyImportBatch` record in `PENDING` state
- **AND** the file is processed asynchronously by a background worker

#### Scenario: Import task completes successfully
- **GIVEN** a `CompanyImportBatch` in `PROCESSING` state
- **WHEN** the background worker finishes importing all valid rows
- **THEN** the batch status changes to `COMPLETED`
- **AND** the batch record contains the count of created and updated companies

#### Scenario: Import task encounters an error
- **GIVEN** a `CompanyImportBatch` in `PROCESSING` state
- **WHEN** the background worker encounters an unrecoverable error (e.g. invalid file format)
- **THEN** the batch status changes to `FAILED`
- **AND** the error details are recorded on the batch record

## MODIFIED Requirements
### Requirement: Enhanced Spanish XLSX Importer
The system SHALL support importing companies from an Excel file using Spanish headers and specific business logic for Spanish data.
The importer MUST process rows within a background task context and:
1. Map `EMPRESA` to `name`, `ACTIVIDAD` to `area`, `DIRECCION` to `address`, `CP` to `zip_code`, `POBLACION` to `location`, `PROVINCIA` to `province`, `COMUNIDAD` to `community`, `TELEFONO` to `phone`, `FAX` to `fax`, `EMAIL` to `email`, and `WEBSITE` to `website`.
2. Split the `ACTIVIDAD` field by the first colon (`:`) and use only the first part as the `Area` name.
3. Normalize all imported string data to lowercase.

#### Scenario: Importer splits ACTIVIDAD and lowercases data
- **GIVEN** an Excel row with `EMPRESA = "KIKO MILANO"`, `ACTIVIDAD = "COSMETICOS: ESTABLECIMIENTOS"`, and `POBLACION = "TORREVIEJA"`
- **WHEN** the file is imported
- **THEN** a `Company` is created with name `"kiko milano"`
- **AND** it is linked to an `Area` named `"cosmeticos"`
- **AND** it is linked to a `Location` named `"torrevieja"`.