import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.mailing.models import MailingLog

from .models import CreditPackage, StripePayment

stripe.api_key = settings.STRIPE_SECRET_KEY


def packages(request):
    active_packages = CreditPackage.objects.filter(is_active=True)
    successful_sends_count = MailingLog.objects.filter(status=MailingLog.Status.SENT).count()
    return render(request, "payments/packages.html", {
        "packages": active_packages,
        "successful_sends_count": successful_sends_count,
    })


@login_required
@require_POST
def create_checkout(request, package_id):
    package = get_object_or_404(CreditPackage, pk=package_id, is_active=True)

    base_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"FastJob — {package.name}"},
                    "unit_amount": package.price_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{base_url}/payments/success/?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/payments/paquetes/",
        metadata={
            "user_id": str(request.user.pk),
            "package_id": str(package.pk),
        },
        customer_email=request.user.email,
    )

    StripePayment.objects.create(
        user=request.user,
        package=package,
        stripe_session_id=session.id,
        amount_eur=package.price_eur,
        credits_granted=package.credits,
    )

    return redirect(session.url)


@login_required
def payment_success(request):
    session_id = request.GET.get("session_id")
    payment = None
    if session_id:
        payment = StripePayment.objects.filter(
            stripe_session_id=session_id, user=request.user
        ).first()
    return render(request, "payments/success.html", {"payment": payment})


@login_required
@require_POST
def billing_portal(request):
    """
    Redirect to Stripe's hosted Billing Portal. Uses the cached
    User.stripe_customer_id when available, otherwise falls back to a
    search-by-email (populates the field on success).
    """
    has_completed = StripePayment.objects.filter(
        user=request.user,
        status=StripePayment.Status.COMPLETED,
    ).exists()
    if not has_completed:
        messages.error(request, "Todavía no tienes pagos completados.")
        return redirect("dashboard")

    customer_id = request.user.stripe_customer_id
    if not customer_id:
        customers = stripe.Customer.list(email=request.user.email, limit=1)
        if not customers.data:
            messages.error(request, "No se encontró una cuenta de facturación asociada a tu email.")
            return redirect("dashboard")
        customer_id = customers.data[0].id
        request.user.stripe_customer_id = customer_id
        request.user.save(update_fields=["stripe_customer_id"])

    return_url = f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}/dashboard/"

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return redirect(session.url)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_successful_payment(session)

    return HttpResponse(status=200)


def _handle_successful_payment(session):
    from apps.accounts.models import User

    session_id = session["id"]
    payment = StripePayment.objects.filter(stripe_session_id=session_id).first()
    if not payment or payment.status == StripePayment.Status.COMPLETED:
        return

    payment.status = StripePayment.Status.COMPLETED
    payment.stripe_payment_intent = session.get("payment_intent", "")
    payment.completed_at = timezone.now()
    payment.save(update_fields=["status", "stripe_payment_intent", "completed_at"])

    user = payment.user
    if user:
        from django.db.models import Case, When, Value
        # Atomic increment: total_purchased_credits is always increased.
        # For credits_remaining, we "forgive" the debt if it's negative by
        # adding the absolute value of the negative balance in addition to the
        # granted credits, ensuring the final balance is at least the granted amount.
        update_kwargs = {
            "credits_remaining": F("credits_remaining") + payment.credits_granted + Case(
                When(credits_remaining__lt=0, then=-F("credits_remaining")),
                default=Value(0)
            ),
            "total_purchased_credits": F("total_purchased_credits") + payment.credits_granted
        }
        # Cache the Stripe customer ID the first time we see it so future
        # billing_portal visits skip the Customer.list() lookup.
        customer = session.get("customer")
        if customer and not user.stripe_customer_id:
            update_kwargs["stripe_customer_id"] = customer
        User.objects.filter(pk=user.pk).update(**update_kwargs)
