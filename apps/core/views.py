from django.views.generic import TemplateView

from apps.mailing.models import MailingLog, SystemSettings
from apps.payments.models import CreditPackage


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = list(
            CreditPackage.objects.filter(is_active=True).order_by("price_eur")
        )
        real_count = MailingLog.objects.filter(status=MailingLog.Status.SENT).count()
        floor = SystemSettings.get().displayed_sends_floor
        context["successful_sends_count"] = max(real_count, floor)
        return context


class PrivacyView(TemplateView):
    template_name = "legal/privacy.html"


class TermsView(TemplateView):
    template_name = "legal/terms.html"
