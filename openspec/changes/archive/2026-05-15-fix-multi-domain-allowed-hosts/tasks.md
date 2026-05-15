# Tasks

## 1. Docker Compose: make host vars overrideable

- [x] 1.1 In `docker-compose.yml` `web.environment`, change line 52 to
      `ALLOWED_HOSTS=${ALLOWED_HOSTS:-${SERVICE_FQDN_WEB},localhost,127.0.0.1}`.
- [x] 1.2 In `docker-compose.yml` `web.environment`, change line 68 to
      `SITE_DOMAIN=${SITE_DOMAIN:-${SERVICE_FQDN_WEB}}`.
- [x] 1.3 In `docker-compose.yml` `web.environment`, change line 90 to
      `CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS:-https://${SERVICE_FQDN_WEB}}`.
- [x] 1.4 Apply the same `${VAR:-…}` override pattern to `SITE_DOMAIN` in the
      `celery_worker.environment` block (line 117 — `SITE_DOMAIN=${SITE_DOMAIN:-${SERVICE_FQDN_WEB}}`).
      It MUST resolve to the same value as the `web` service, otherwise unsubscribe
      links and other absolute URLs built from background tasks will drift to the
      Coolify subdomain. Do NOT add `ALLOWED_HOSTS` or `CSRF_TRUSTED_ORIGINS` to celery
      services — they do not serve HTTP and those settings are inert there.
- [x] 1.5 Apply the same `${VAR:-…}` override pattern to `SITE_DOMAIN` in the
      `celery_beat.environment` block (line 151). Same scope rules as 1.4.

## 2. Documentation

- [x] 2.1 Update `.env.example` with a brief header comment above the three keys
      (`ALLOWED_HOSTS`, `SITE_DOMAIN`, `CSRF_TRUSTED_ORIGINS`) explaining that:
      (a) for local dev these defaults work as-is;
      (b) for Coolify/production, set them in the Coolify UI to enable additional
      public domains beyond the auto-derived `SERVICE_FQDN_WEB`.
- [x] 2.2 If a deployment doc/README section exists for Coolify (search
      `rg -n "Coolify" README.md docs/` first), add a "Multi-domain deployment"
      sub-section listing the exact UI variables to set. If no such doc exists,
      skip — do not introduce a new doc file just for this.

## 3. Local development verification

- [x] 3.1 With the existing developer `.env` (which sets
      `ALLOWED_HOSTS=localhost,127.0.0.1,fastjob.localhost`), run
      `docker compose config | grep -E 'ALLOWED_HOSTS|SITE_DOMAIN|CSRF_TRUSTED_ORIGINS'`
      and confirm the values resolve to the `.env` overrides — not to a fallback path
      using a missing `SERVICE_FQDN_WEB`.
- [x] 3.2 With the override vars *unset* (simulate a fresh Coolify import by exporting
      only `SERVICE_FQDN_WEB=fastjob-xyz.coolify.io`), run the same
      `docker compose config` and confirm the rendered values match today's behavior
      byte-for-byte (no regression for the existing
      `Coolify One-Click Compatibility` requirement).
- [x] 3.3 Run the test suite (`pytest`) to confirm no settings-import regression.

## 4. Production rollout (operator runbook — to be executed by the operator in Coolify)

> These steps live outside this repo's reach (Coolify UI + live production). Left
> unchecked intentionally; the operator should tick them off after they perform the
> rollout. The repository-side enabler (compose `${VAR:-…}` form) is already in place
> via §1.

- [ ] 4.1 In Coolify → Project → Environment variables, declare (Runtime checked):
      - `ALLOWED_HOSTS=fastjob.es,fastjob.apps.darideveloper.com,localhost,127.0.0.1`
      - `CSRF_TRUSTED_ORIGINS=https://fastjob.es,https://fastjob.apps.darideveloper.com`
      - `SITE_DOMAIN=fastjob.es`
- [ ] 4.2 Click **Redeploy** in Coolify.
- [ ] 4.3 Verify with `curl -sI https://fastjob.es/ | head -1` → `HTTP/2 200`
      (or a redirect), not `HTTP/2 400`.
- [ ] 4.4 Verify with `curl -sI https://fastjob.apps.darideveloper.com/ | head -1`
      → still 200 (no regression on the original domain).
- [ ] 4.5 Inside the running web container, run
      `python -c "from django.conf import settings; print(settings.ALLOWED_HOSTS, settings.CSRF_TRUSTED_ORIGINS, settings.SITE_DOMAIN)"`
      and confirm the three values include both public domains.
- [ ] 4.6 Smoke-test a CSRF-protected POST from `fastjob.es` (e.g. profile save) and
      trigger one transactional email (password reset is fastest) to confirm
      `SITE_DOMAIN` propagated to absolute URLs.

## 5. Spec & validation

- [x] 5.1 Update `specs/infrastructure/spec.md` per the delta in
      `changes/fix-multi-domain-allowed-hosts/specs/infrastructure/spec.md`.
- [x] 5.2 Run `openspec validate fix-multi-domain-allowed-hosts --strict` and resolve
      any reported issues.
