import logging

from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_removed
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import CV


logger = logging.getLogger(__name__)

SIGNUP_BONUS_CREDITS = 5


@receiver(pre_delete, sender=CV)
def cv_pre_delete(sender, instance, **kwargs):
    """C9: drop the S3 object when its CV row is removed.

    The previous `CV.delete()` override only ran for per-instance deletes —
    `User.delete()` cascade and admin bulk `QuerySet.delete()` skip it,
    leaking orphans into the bucket. `pre_delete` fires for every code path
    (instance, cascade, queryset bulk), so this is the right hook.
    """
    if instance.file:
        instance.file.delete(save=False)
@receiver(user_signed_up)
def grant_signup_bonus(sender, request, user, **kwargs):
    """Give every new user a handful of free credits so they can try the product."""
    from apps.mailing.models import SystemSettings
    if user.credits_remaining == 0:
        cfg = SystemSettings.get()
        user.credits_remaining = cfg.initial_free_credits
        user.save(update_fields=["credits_remaining"])

@receiver(social_account_removed)
def pause_campaign_on_unlink(sender, request, socialaccount, **kwargs):
    """
    If a user disconnects their OAuth account, we can no longer send on their
    behalf. Auto-pause the campaign so the engine doesn't churn through FAILED
    MailingLog rows on every tick.
    """
    user = socialaccount.user
    if user.is_campaign_active:
        user.is_campaign_active = False
        user.campaign_pause_reason = "unlinked"
        user.save(update_fields=["is_campaign_active", "campaign_pause_reason"])
        logger.info("Campaign paused for user_pk=%s after OAuth unlink (%s)", user.pk, socialaccount.provider)
