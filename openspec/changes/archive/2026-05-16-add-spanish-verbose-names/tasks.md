# Tasks: Add Spanish verbose names to all admin-facing model fields

## 1. Mailing app — models.py

- [x] 1.1 Add `verbose_name` to `SystemSettings.global_send_interval_minutes` → `"Intervalo de envío (minutos)"`
- [x] 1.2 Add `verbose_name` to `SystemSettings.company_cooldown_hours` → `"Enfriamiento por empresa (horas)"`
- [x] 1.3 Add `verbose_name` to `SystemSettings.max_emails_per_day_per_user` → `"Máximo de envíos por usuario al día"`
- [x] 1.4 Add `verbose_name` to `SystemSettings.initial_free_credits` → `"Envíos gratuitos iniciales"`
- [x] 1.5 Add `verbose_name` to `SystemSettings.hidden_credit_multiplier` → `"Multiplicador oculto de envíos"`
- [x] 1.6 Add `verbose_name` to `EmailTemplate.name` → `"Nombre"`
- [x] 1.7 Add `verbose_name` to `EmailTemplate.subject` → `"Asunto"`
- [x] 1.8 Add `verbose_name` to `EmailTemplate.body_html` → `"Cuerpo HTML"`
- [x] 1.9 Add `verbose_name` to `EmailTemplate.is_active` → `"Activa"`
- [x] 1.10 Add `verbose_name` to `EmailTemplate.created_at` → `"Creada el"`
- [x] 1.11 Add `verbose_name` to `MailingLog.user` → `"Usuario"`
- [x] 1.12 Add `verbose_name` to `MailingLog.company` → `"Empresa"`
- [x] 1.13 Add `verbose_name` to `MailingLog.email_template` → `"Plantilla de email"`
- [x] 1.14 Add `verbose_name` to `MailingLog.cv` → `"CV"`
- [x] 1.15 Add `verbose_name` to `MailingLog.cv_download_token` → `"Token de descarga del CV"`
- [x] 1.16 Add `verbose_name` to `MailingLog.unsubscribe_token` → `"Token de baja"`
- [x] 1.17 Add `verbose_name` to `MailingLog.sent_at` → `"Enviado el"`
- [x] 1.18 Add `verbose_name` to `MailingLog.status` → `"Estado"`
- [x] 1.19 Add `verbose_name` to `MailingLog.error_message` → `"Mensaje de error"`
- [x] 1.20 Add `verbose_name` to `MailingLog.company_email_snapshot` → `"Email de la empresa"`
- [x] 1.21 Add `verbose_name` to `MailingLog.unsubscribed_at` → `"Fecha de baja"`

## 2. Mailing app — admin.py

- [x] 2.1 Replace `SystemSettingsAdmin` first fieldset `description` — remove Python key names, rewrite as pure Spanish prose
- [x] 2.2 Replace `SystemSettingsAdmin` second fieldset `description` — remove Python key names, rewrite as pure Spanish prose
- [x] 2.3 Change `preview_link.short_description` from `"Preview"` to `"Vista previa"`

## 3. Accounts app — models.py

- [x] 3.1 Add `verbose_name` to `User.is_campaign_active` → `"Campaña activa"`
- [x] 3.2 Add `verbose_name` to `User.active_cv` → `"CV activo"`
- [x] 3.3 Add `verbose_name` to `User.area_filters` → `"Filtros de sector"`
- [x] 3.4 Add `verbose_name` to `User.location_filters` → `"Filtros de localidad"`
- [x] 3.5 Add `verbose_name` to `User.stripe_customer_id` → `"ID de cliente Stripe"`
- [x] 3.6 Add `verbose_name` to `CV.user` → `"Usuario"`
- [x] 3.7 Add `verbose_name` to `CV.file` → `"Archivo"`
- [x] 3.8 Add `verbose_name` to `CV.name` → `"Nombre"`
- [x] 3.9 Add `verbose_name` to `CV.created_at` → `"Creado el"`

## 4. Accounts app — admin.py

- [x] 4.1 Change `UserAdmin` fieldset header `"FastJob"` → `"Datos FastJob"`

## 5. Companies app — models.py

- [x] 5.1 Add `verbose_name` to `Area.name` → `"Nombre"`
- [x] 5.2 Add `verbose_name` to `Location.name` → `"Nombre"`
- [x] 5.3 Add `verbose_name` to `Company.email` → `"Email"`
- [x] 5.4 Add `verbose_name` to `Company.name` → `"Nombre"`
- [x] 5.5 Add `verbose_name` to `Company.area` → `"Sector"`
- [x] 5.6 Add `verbose_name` to `Company.location` → `"Localidad"`
- [x] 5.7 Add `verbose_name` to `Company.address` → `"Dirección"`
- [x] 5.8 Add `verbose_name` to `Company.zip_code` → `"Código postal"`
- [x] 5.9 Add `verbose_name` to `Company.province` → `"Provincia"`
- [x] 5.10 Add `verbose_name` to `Company.community` → `"Comunidad"`
- [x] 5.11 Add `verbose_name` to `Company.phone` → `"Teléfono"`
- [x] 5.12 Add `verbose_name` to `Company.fax` → `"Fax"`
- [x] 5.13 Add `verbose_name` to `Company.website` → `"Sitio web"`
- [x] 5.14 Add `verbose_name` to `Company.last_received_at` → `"Último envío recibido"`
- [x] 5.15 Add `verbose_name` to `Company.created_at` → `"Creada el"`
- [x] 5.16 Add `verbose_name` to `Blacklist.email` → `"Email"`
- [x] 5.17 Add `verbose_name` to `Blacklist.added_at` → `"Añadido el"`
- [x] 5.18 Add `verbose_name` to `Blacklist.reason` → `"Motivo"`
- [x] 5.19 Add `verbose_name` to `CompanyImportBatch.file` → `"Archivo"`
- [x] 5.20 Add `verbose_name` to `CompanyImportBatch.status` → `"Estado"`
- [x] 5.21 Add `verbose_name` to `CompanyImportBatch.upload_uuid` → `"UUID de subida"`
- [x] 5.22 Add `verbose_name` to `CompanyImportBatch.original_filename` → `"Nombre de archivo original"`
- [x] 5.23 Add `verbose_name` to `CompanyImportBatch.total_rows` → `"Total de filas"`
- [x] 5.24 Add `verbose_name` to `CompanyImportBatch.processed_rows` → `"Filas procesadas"`
- [x] 5.25 Add `verbose_name` to `CompanyImportBatch.created_count` → `"Empresas creadas"`
- [x] 5.26 Add `verbose_name` to `CompanyImportBatch.updated_count` → `"Empresas actualizadas"`
- [x] 5.27 Add `verbose_name` to `CompanyImportBatch.blacklisted_skipped` → `"Omitidas (lista negra)"`
- [x] 5.28 Add `verbose_name` to `CompanyImportBatch.error_log` → `"Registro de errores"`
- [x] 5.29 Add `verbose_name` to `CompanyImportBatch.created_at` → `"Creada el"`
- [x] 5.30 Add `verbose_name` to `CompanyImportBatch.updated_at` → `"Actualizada el"`

## 6. Payments app — models.py

- [x] 6.1 Add `verbose_name` to `StripePayment.user` → `"Usuario"`
- [x] 6.2 Add `verbose_name` to `StripePayment.package` → `"Paquete"`
- [x] 6.3 Add `verbose_name` to `StripePayment.stripe_session_id` → `"ID de sesión Stripe"`
- [x] 6.4 Add `verbose_name` to `StripePayment.stripe_payment_intent` → `"Payment intent Stripe"`
- [x] 6.5 Add `verbose_name` to `StripePayment.amount_eur` → `"Importe (€)"`
- [x] 6.6 Add `verbose_name` to `StripePayment.credits_granted` → `"Envíos otorgados"`
- [x] 6.7 Add `verbose_name` to `StripePayment.status` → `"Estado"`
- [x] 6.8 Add `verbose_name` to `StripePayment.created_at` → `"Creado el"`
- [x] 6.9 Add `verbose_name` to `StripePayment.completed_at` → `"Completado el"`

## 7. Core app — models.py

- [x] 7.1 Add `verbose_name="Guardar en carpeta Enviados"` to `SystemConfig.save_emails_to_sent_folder`
- [x] 7.2 Remove the trailing `(Sent)` from `SystemConfig.save_emails_to_sent_folder.help_text`

## 8. Validation

- [ ] 8.1 Start Django dev server and open `/admin/` — verify no English field labels remain
- [ ] 8.2 Open `/admin/mailing/systemsettings/1/change/` — verify all 5 field labels are Spanish and fieldset descriptions contain no Python identifiers
- [ ] 8.3 Open `/admin/accounts/user/` — verify fieldset header reads "Datos FastJob" and all User fields are Spanish
- [ ] 8.4 Open `/admin/mailing/emailtemplate/` — verify column "Vista previa" (not "Preview")
- [x] 8.5 Run `python manage.py check` — confirm zero system check errors
