# FastJob

Django SaaS que envía CVs a bases de datos de empresas desde la **propia cuenta de Gmail u Outlook del usuario** vía OAuth2. Diseñada para máxima entregabilidad (sin adjuntos, slow-drip, plantillas aleatorias).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Django 4.2 (SSR) |
| DB | PostgreSQL |
| Queue | Celery + Redis |
| Auth | django-allauth (Google `gmail.send`, Microsoft `Mail.Send`) |
| Storage | DigitalOcean Spaces (S3 compatible) |
| Payments | Stripe (EUR) |
| Frontend | Server-rendered + Tailwind CDN |

## Local setup

Requisitos previos: tener instalado `tmux` y `npm` (para `localtunnel`).

```bash
git clone <repo> fastjob && cd fastjob
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # editar con tus credenciales

# levanta Postgres + Redis con Docker
docker-compose up -d db redis

python manage.py migrate
python manage.py createsuperuser
python manage.py setup_periodic_tasks   # registra la tarea de Celery en la DB

# Levanta todos los servicios de desarrollo (Django, Celery, Stripe CLI y Localtunnel)
./dev.sh
```

El entorno local estará disponible **exclusivamente** a través de `https://fastjob.loca.lt` (sin puertos adicionales). Asegúrate de usar esta URL para acceder a la aplicación y configurar los Webhooks y OAuth redirects.

## Configuración de servicios externos

### Google OAuth2 (Gmail Send)

1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com).
2. APIs & Services → Library → habilita **Gmail API**.
3. APIs & Services → OAuth consent screen → External → añade el scope `https://www.googleapis.com/auth/gmail.send`.
4. Credentials → Create Credentials → OAuth client ID → Web application.
5. Authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
6. Copia `client_id` y `secret` a `.env` (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`).

> **Importante:** el ajuste `access_type=offline` + `prompt=consent` ya está configurado en `settings.py`. Sin ello, Google no emite refresh tokens y el motor dejará de funcionar cuando expire el access token (normalmente a la hora).

> **Producción vs Testing:** mientras la pantalla de consentimiento esté en estado **Testing**, los refresh tokens de Google caducan a los **7 días** sin importar la actividad del usuario. Antes de desplegar a producción, mueve la consent screen a **Production**. La variable de entorno `GOOGLE_OAUTH_PROJECT_MODE=testing` hace que `/healthz` emita un warning recordándolo.

### Microsoft OAuth2 (Graph Mail.Send)

1. Azure Portal → App registrations → New registration.
2. Redirect URI: `http://localhost:8000/accounts/microsoft/login/callback/`
3. API permissions → Microsoft Graph → Delegated → `Mail.Send`, `User.Read`, `offline_access`.
4. Certificates & secrets → New client secret → copia el valor inmediatamente.
5. Copia los valores a `.env` (`MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`).
6. Si registraste la app como **single-tenant**, fija `MICROSOFT_TENANT=<tu-tenant-guid>` en `.env`. Por defecto el motor usa `common` (multi-tenant + cuentas personales) — usar `common` con una app single-tenant produce un `400 invalid_grant` en cada refresh.

### OAuth — variables operacionales

| Variable | Valor por defecto | Cuándo cambiarla |
|---|---|---|
| `GOOGLE_OAUTH_PROJECT_MODE` | `production` | Pon `testing` mientras la consent screen no esté aprobada. `/healthz` mostrará un warning. |
| `MICROSOFT_TENANT` | `common` | Pon el tenant GUID si la app de Azure es single-tenant. |

Verifica la configuración antes de cada deploy:

```bash
python manage.py check_oauth_config
```

Sale con código no-cero si Microsoft no resuelve o Google está caído. Para confirmar que la rotación de refresh tokens funciona en producción, busca en los logs líneas con `outcome=rotated provider=microsoft` después del primer refresh post-deploy.

### Stripe

1. [Dashboard Stripe](https://dashboard.stripe.com) → API keys → copia `sk_test_...` y `pk_test_...`.
2. Webhooks → Add endpoint → URL: `https://<tu-dominio>/payments/webhook/` → evento `checkout.session.completed`.
3. Copia el webhook secret (`whsec_...`) a `.env`.

### DigitalOcean Spaces

1. [DO Spaces](https://cloud.digitalocean.com/spaces) → Create a Space.
2. API → Generate new Spaces key.
3. Rellena `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME` en `.env`.

## Uso diario

### Como admin (Django Admin)

- **Empresas → Importar desde Excel** — sube un `.xlsx` con columnas `name`, `email` (opcionales: `area`, `location`).
- **Plantillas de Email** — añade nuevas variantes. Usa `{company_name}`, `{cv_url}`, `{unsubscribe_url}` como placeholders.
- **Configuración del Sistema** — edita el intervalo de envío (5 min por defecto) y el cooldown por empresa (12 horas por defecto).
- **Paquetes de Créditos** — ajusta precios en EUR y cantidad de créditos; pega el `stripe_price_id` si usas Stripe Prices en vez de precios dinámicos.
- **Lista Negra** — emails que hicieron click en "unsubscribe"; gestiona o elimina manualmente si es necesario.

### Como usuario

1. Inicia sesión con Google/Microsoft.
2. Sube tu CV (PDF, máx 10 MB).
3. (Opcional) Filtra por sector y ubicación.
4. Compra créditos.
5. Pulsa **Iniciar campaña**. Cada 5 min se envía un email desde tu cuenta.

## Arquitectura del motor de envío

```
Celery beat (cada 1 min)
  └─> process_mailing_queue
        └─> por cada User activo con créditos:
              ├─ ¿Pasaron ≥ 5 min desde su último envío?  → no → skip
              ├─ Empresas candidatas = all − blacklist − enviadas hace < 12h − filtros
              ├─ Plantilla = EmailTemplate.objects.order_by('?').first()
              ├─ MailingLog.objects.create(...)  → genera tokens UUID
              ├─ engine.send_cv_email()
              │    ├─ refresh OAuth token si necesita
              │    ├─ Gmail API o Microsoft Graph
              │    └─ body HTML con {cv_url}, {unsubscribe_url}
              └─ -1 crédito + last_received_at = now
```

Si el token OAuth expira irremediablemente, la campaña del usuario se pausa y recibe un email de re-link.

## Tests

```bash
pytest    # pendiente de implementar — ver log.md
```

## Producción

- Asegúrate de `DEBUG=False`, `ALLOWED_HOSTS` correcto, `SECRET_KEY` rotado.
- Redirect URIs en Google/Microsoft → URL HTTPS real.
- Celery beat + worker **deben** estar corriendo, o no se envía nada.
- Configura `SECURE_PROXY_SSL_HEADER` si estás detrás de un reverse proxy.

## Ver también

- [`log.md`](log.md) — registro de cambios y tareas pendientes.
