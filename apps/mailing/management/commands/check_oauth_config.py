"""
``manage.py check_oauth_config`` — fail-loud deploy guardrail.

Verifies that the configured Microsoft tenant resolves and that the Google
token endpoint is reachable. Exits non-zero on any failure so deployment
pipelines can gate on it. Does NOT call OAuth itself — it only checks that the
provider-side config the engine depends on is wired correctly.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify OAuth provider configuration is reachable and well-formed."

    def handle(self, *args, **options):
        failures = []

        tenant = getattr(settings, "MICROSOFT_TENANT", "common") or "common"
        ms_url = (
            f"https://login.microsoftonline.com/{tenant}"
            "/v2.0/.well-known/openid-configuration"
        )
        try:
            resp = requests.get(ms_url, timeout=10)
            if resp.status_code != 200:
                failures.append(
                    f"Microsoft tenant '{tenant}' discovery returned "
                    f"HTTP {resp.status_code} from {ms_url}"
                )
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"OK Microsoft tenant '{tenant}' discovery reachable."
                ))
        except requests.RequestException as exc:
            failures.append(f"Microsoft tenant '{tenant}' unreachable: {exc}")

        google_url = "https://oauth2.googleapis.com/token"
        try:
            # POST with no body; expect 4xx (bad request) — that confirms the
            # endpoint exists. A 5xx or network error means Google itself is
            # unreachable from this host.
            resp = requests.post(google_url, data={}, timeout=10)
            if resp.status_code >= 500:
                failures.append(
                    f"Google token endpoint returned HTTP {resp.status_code}"
                )
            else:
                self.stdout.write(self.style.SUCCESS(
                    "OK Google token endpoint reachable."
                ))
        except requests.RequestException as exc:
            failures.append(f"Google token endpoint unreachable: {exc}")

        project_mode = getattr(settings, "GOOGLE_OAUTH_PROJECT_MODE", "production")
        if str(project_mode).lower() == "testing":
            self.stdout.write(self.style.WARNING(
                "WARN GOOGLE_OAUTH_PROJECT_MODE=testing — refresh tokens "
                "expire after 7 days."
            ))

        if failures:
            for line in failures:
                self.stderr.write(self.style.ERROR(line))
            # Non-zero exit so CI/CD can gate on it.
            raise SystemExit(1)
