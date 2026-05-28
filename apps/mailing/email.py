from django.template.loader import render_to_string
from apps.mailing.models import SystemSettings

def render_branded_email(subject, body_html, context=None):
    cfg = SystemSettings.get()
    full_context = {
        "subject": subject,
        "body_html": body_html,
        "logo_url": cfg.email_logo_url,
        "brand_color": cfg.email_brand_color,
        "footer_text": cfg.email_footer_text,
    }
    if context:
        full_context.update(context)
    return render_to_string("email/base.html", full_context)
