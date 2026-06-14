from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from apps.mailing.models import MailingLog, SystemSettings
from apps.payments.models import CreditPackage
from .models import FAQ


class MicrosoftIdentityAssociationView(View):
    def get(self, request, *args, **kwargs):
        data = {
            "associatedApplications": [
                {"applicationId": "3853b95b-027f-4c59-94e4-d697b2a603a9"}
            ]
        }
        return JsonResponse(data)


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
        context["faqs"] = list(
            FAQ.objects.filter(is_active=True).order_by("order")
        )
        return context


class PrivacyView(TemplateView):
    def get_template_names(self):
        if self.request.resolver_match and self.request.resolver_match.url_name == "privacy_en":
            return ["legal/privacy_en.html"]
        return ["legal/privacy.html"]


class TermsView(TemplateView):
    def get_template_names(self):
        if self.request.resolver_match and self.request.resolver_match.url_name == "terms_en":
            return ["legal/terms_en.html"]
        return ["legal/terms.html"]
