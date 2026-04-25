import logging

from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_removed
from django.dispatch import receiver


logger = logging.getLogger(__name__)

SIGNUP_BONUS_CREDITS = 5


@receiver(user_signed_up)
def grant_signup_bonus(sender, request, user, **kwargs):
    """Give every new user a handful of free credits so they can try the product."""
    if user.credits_remaining == 0:
        user.credits_remaining = SIGNUP_BONUS_CREDITS
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
        user.save(update_fields=["is_campaign_active"])
        logger.info("Campaign paused for user_pk=%s after OAuth unlink (%s)", user.pk, socialaccount.provider)
