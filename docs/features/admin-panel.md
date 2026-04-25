# Admin Panel

ResumeLink's admin is standard Django Admin (`/admin/`) with custom list views and the Excel importer. Only `is_staff = True` users can access it. It's the primary operational interface for everything that isn't user-facing.

---

## Access

`/admin/` requires `is_staff = True`. Create a superuser:

```bash
python manage.py createsuperuser
```

In production, restrict `/admin/` at the load-balancer or firewall level — don't expose it publicly.

## GDPR deletion (CLI)

To delete a user and all their data from a shell:

```bash
python manage.py delete_user --email ana@example.com          # interactive prompt
python manage.py delete_user --email ana@example.com --yes    # skip confirmation (scripted use)
```

Removes the `User` row (cascades to `MailingLog`, `SocialAccount`, `SocialToken`) and explicitly deletes each `CV` file from Spaces. `StripePayment` rows are `SET_NULL`-preserved for accounting.

Users can also delete themselves from the dashboard (**Zona peligrosa → Eliminar mi cuenta**), which requires them to type their own email to confirm.

---

## Admin sections at a glance

| Section | Model(s) | Key operations |
|---|---|---|
| **Usuarios** | `accounts.User` | View/edit credits, CV link, filter fields, campaign status, OAuth provider |
| **Social Accounts** | allauth's `SocialAccount`, `SocialToken` | Debug OAuth links; rarely needed |
| **Empresas** | `companies.Company` | CRUD, Excel import, filter by area/location |
| **Lista Negra** | `companies.Blacklist` | Add/remove blacklist entries, view unsubscribes |
| **Plantillas de Email** | `mailing.EmailTemplate` | CRUD templates; toggle `is_active` |
| **Configuración del Sistema** | `mailing.SystemSettings` | Slow-drip interval, company cooldown |
| **Registros de Envíos** | `mailing.MailingLog` | Read-only audit log of every send |
| **Paquetes de Créditos** | `payments.CreditPackage` | Create/edit/deactivate packages |
| **Pagos Stripe** | `payments.StripePayment` | Read-only payment audit trail |
| **Periodic Tasks** (django-celery-beat) | `django_celery_beat.PeriodicTask` | Beat schedule management |

---

## Usuarios (`accounts.User`)

**List columns:** email, `credits_remaining`, `is_campaign_active`, OAuth provider (derived from `socialaccount_set`), `date_joined`.

**Useful operations:**
- Manually adjust `credits_remaining` for support cases.
- Clear `cv_file` if a user needs to re-upload (e.g. corrupted file).
- Set `is_campaign_active = False` to force-pause a campaign.
- Check which OAuth provider is linked (Google / Microsoft / none).

**What you cannot do here:**
- See or modify OAuth token values (intentional — security).
- Impersonate a user (no impersonation feature, P2 item).

---

## Empresas — Excel Import

The most common admin operation. See [`companies.md`](companies.md) for full importer docs.

**Quick how-to:**
1. `Django Admin → Empresas → Empresas`.
2. Click "Importar Excel" (top-right).
3. Upload `.xlsx` with columns: `name`, `email`, (optional) `area`, `location`.
4. Review the success + warning messages.

**Repeat imports are safe** — `update_or_create` on `email` means duplicates are updated, not double-inserted.

---

## Lista Negra (`companies.Blacklist`)

Automatically populated when a recipient clicks "unsubscribe" in an email. Can also be managed manually:
- **Add:** to pre-emptively exclude a company (e.g. a competitor, a company that requested removal by email).
- **Delete:** to un-blacklist a company. Only do this if you have explicit consent from the company.

`reason` field values:
- `"unsubscribe"` — set by the unsubscribe view (default).
- Any custom string for admin-added entries (e.g. `"manual"`, `"gdpr-request"`).

---

## Plantillas de Email (`mailing.EmailTemplate`)

The engine's variation pool. See [`email-templates.md`](email-templates.md) for full docs.

**Key operations:**
- Toggle `is_active` to add/remove a template from the random pool immediately.
- Edit `subject` and `body_html` (raw HTML). Changes apply to all future sends — no restart needed.
- The 3 default templates are a good baseline; feel free to add more.

**Minimum:** 1 active template must exist at all times or the engine sends nothing.

---

## Configuración del Sistema (`mailing.SystemSettings`)

A singleton row (pk=1 is enforced; delete is a no-op). Two settings:

| Setting | Default | Effect |
|---|---|---|
| `global_send_interval_minutes` | 5 | Minimum minutes between two sends for the same user |
| `company_cooldown_hours` | 12 | Hours before a company can receive another CV (any user) |

**Changes take effect on the next beat tick** (≤ 1 minute). No restart needed.

---

## Registros de Envíos (`mailing.MailingLog`)

Read-only in admin. Use it to:
- Investigate a specific user complaint ("I never got sends this morning").
- Filter by `status = FAILED` to see recent engine errors.
- Search by recipient email to confirm a specific company was contacted.

---

## Paquetes de Créditos (`payments.CreditPackage`)

Create and manage what's shown on the `/payments/paquetes/` page.

- `is_active = False` hides the package from users immediately.
- `order` controls display order (ascending).
- `stripe_price_id` is optional — the current checkout flow uses dynamic pricing and doesn't require it.
- **Never delete** a package with associated `StripePayment` rows — prefer `is_active = False`.

Default seeded packages: Starter (50 credits, €9.99), Pro (200 credits, €29.99), Elite (600 credits, €69.99).

---

## Pagos Stripe (`payments.StripePayment`)

Read-only. Used to:
- Verify a user's payment history.
- Cross-reference `stripe_session_id` with the Stripe dashboard.
- Check for stuck `PENDING` payments (user abandoned checkout).

---

## Periodic Tasks (django-celery-beat)

The beat scheduler is configured via the database. After first deploy, register the mailing task:

```bash
python manage.py setup_periodic_tasks
```

This creates an `IntervalSchedule` (1 minute) and a `PeriodicTask` pointing at `apps.mailing.tasks.process_mailing_queue`.

You can view and edit the task in `Django Admin → Periodic Tasks → Periodic Tasks`. Changing the interval there takes effect on the next beat poll (usually within 5 seconds).

**Warning:** never run two `celery beat` processes — the task fires twice per interval. The `docker-compose.yml` enforces a single `celery_beat` service.

---

## Related docs

- [`companies.md`](companies.md) — Excel import details.
- [`email-templates.md`](email-templates.md) — authoring templates.
- [`payments.md`](payments.md) — Stripe package management.
- [`mailing-engine.md`](mailing-engine.md) — `SystemSettings` and how they affect sends.
