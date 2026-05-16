## ADDED Requirements

### Requirement: Spanish verbose names on Area and Location name fields
`Area` and `Location` (`apps/companies/models.py`) SHALL each declare `verbose_name="Nombre"` on their `name` field.

#### Scenario: Area and Location change forms show "Nombre"
- **WHEN** a staff user opens `/admin/companies/area/<id>/change/`
  or `/admin/companies/location/<id>/change/`
- **THEN** the field label reads `"Nombre"` in Spanish

### Requirement: Spanish verbose names on Company fields
`Company` (`apps/companies/models.py`) SHALL declare explicit Spanish `verbose_name` on every field that previously lacked one.

| Field | verbose_name |
|---|---|
| `email` | `"Email"` |
| `name` | `"Nombre"` |
| `area` | `"Sector"` |
| `location` | `"Localidad"` |
| `address` | `"Dirección"` |
| `zip_code` | `"Código postal"` |
| `province` | `"Provincia"` |
| `community` | `"Comunidad"` |
| `phone` | `"Teléfono"` |
| `fax` | `"Fax"` |
| `website` | `"Sitio web"` |
| `last_received_at` | `"Último envío recibido"` |
| `created_at` | `"Creada el"` |

#### Scenario: Company change form shows Spanish field labels
- **WHEN** a staff user opens `/admin/companies/company/<id>/change/`
- **THEN** every field label matches the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Zip code", "Last received at") is visible

### Requirement: Spanish verbose names on Blacklist fields
All fields of `Blacklist` (`apps/companies/models.py`) SHALL declare an
explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `email` | `"Email"` |
| `added_at` | `"Añadido el"` |
| `reason` | `"Motivo"` |

#### Scenario: Blacklist change form shows Spanish field labels
- **WHEN** a staff user opens `/admin/companies/blacklist/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above

### Requirement: Spanish verbose names on CompanyImportBatch fields
All fields of `CompanyImportBatch` (`apps/companies/models.py`) SHALL
declare an explicit `verbose_name` in Spanish.

| Field | verbose_name |
|---|---|
| `file` | `"Archivo"` |
| `status` | `"Estado"` |
| `upload_uuid` | `"UUID de subida"` |
| `original_filename` | `"Nombre de archivo original"` |
| `total_rows` | `"Total de filas"` |
| `processed_rows` | `"Filas procesadas"` |
| `created_count` | `"Empresas creadas"` |
| `updated_count` | `"Empresas actualizadas"` |
| `blacklisted_skipped` | `"Omitidas (lista negra)"` |
| `error_log` | `"Registro de errores"` |
| `created_at` | `"Creada el"` |
| `updated_at` | `"Actualizada el"` |

#### Scenario: CompanyImportBatch change form shows Spanish field labels
- **WHEN** a staff user opens
  `/admin/companies/companyimportbatch/<id>/change/`
- **THEN** each field label matches the Spanish string from the table above
- **AND** no English auto-generated label (e.g. "Upload uuid",
  "Blacklisted skipped") is visible
