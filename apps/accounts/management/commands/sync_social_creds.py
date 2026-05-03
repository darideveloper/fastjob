from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Migrates social credentials from settings to the SocialApp database model."

    def handle(self, *args, **options):
        self.stdout.write("Starting social credentials migration...")

        site_id = getattr(settings, "SITE_ID", 1)
        site, _ = Site.objects.get_or_create(
            id=site_id,
            defaults={"domain": "example.com", "name": "example.com"}
        )

        providers = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})
        
        migrated_count = 0
        for provider, config in providers.items():
            if "APP" in config:
                app_config = config["APP"]
                client_id = app_config.get("client_id")
                secret = app_config.get("secret")
                
                if client_id and secret:
                    # Provide a default name based on the provider
                    name = f"{provider.capitalize()} App"
                    
                    app, created = SocialApp.objects.update_or_create(
                        provider=provider,
                        defaults={
                            "name": name,
                            "client_id": client_id,
                            "secret": secret,
                        }
                    )
                    app.sites.add(site)
                    action = "Created" if created else "Updated"
                    self.stdout.write(self.style.SUCCESS(f"{action} SocialApp for {provider}"))
                    migrated_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"Skipping {provider}: Missing client_id or secret in settings."))
            else:
                self.stdout.write(f"No APP configuration found for {provider}, skipping.")

        self.stdout.write(self.style.SUCCESS(f"Migration complete. Processed {migrated_count} providers."))
