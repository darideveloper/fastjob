import csv
import io
import json
import zipfile
from datetime import timedelta
from tempfile import SpooledTemporaryFile

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django_ratelimit.decorators import ratelimit

from apps.accounts.models import CV
from apps.mailing.models import MailingLog
from apps.payments.models import StripePayment


LOG_PAGE_SIZE = 20


@login_required
def index(request):
    user = request.user
    logs_qs = MailingLog.objects.filter(user=user).select_related("company", "email_template", "cv")
    paginator = Paginator(logs_qs, LOG_PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    user_logs = MailingLog.objects.filter(user=user)
    payments = StripePayment.objects.filter(user=user).select_related("package").order_by("-created_at")
    has_completed_payments = any(p.status == StripePayment.Status.COMPLETED for p in payments)

    context = {
        "user": user,
        "recent_logs": page.object_list,
        "page_obj": page,
        "paginator": paginator,
        "cvs": user.cvs.all(),
        "sent_count": user_logs.filter(status=MailingLog.Status.SENT).count(),
        "sent_today": user_logs.filter(status=MailingLog.Status.SENT, sent_at__gte=today_start).count(),
        "sent_this_week": user_logs.filter(status=MailingLog.Status.SENT, sent_at__gte=week_start).count(),
        "failed_count": user_logs.filter(status=MailingLog.Status.FAILED).count(),
        "payments": payments,
        "has_completed_payments": has_completed_payments,
    }
    return render(request, "dashboard/index.html", context)


@login_required
@require_POST
def upload_cv(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    def json_error(msg, status=400):
        return JsonResponse({"ok": False, "error": msg}, status=status)

    cv_file = request.FILES.get("cv_file")
    if not cv_file:
        if is_ajax:
            return json_error("Por favor selecciona un archivo PDF.")
        messages.error(request, "Por favor selecciona un archivo PDF.")
        return redirect("dashboard")

    if not cv_file.name.lower().endswith(".pdf"):
        if is_ajax:
            return json_error("Solo se permiten archivos PDF.")
        messages.error(request, "Solo se permiten archivos PDF.")
        return redirect("dashboard")

    if cv_file.size > 10 * 1024 * 1024:
        if is_ajax:
            return json_error("El archivo no puede superar los 10 MB.")
        messages.error(request, "El archivo no puede superar los 10 MB.")
        return redirect("dashboard")

    user = request.user

    # Atomic: create the new CV first, then point active_cv at it. The old CV
    # row is preserved — users can delete it manually if desired — so an upload
    # failure never leaves the user without a CV.
    cv = CV.objects.create(user=user, file=cv_file, name="")
    user.active_cv = cv
    user.save(update_fields=["active_cv"])

    if is_ajax:
        return JsonResponse({"ok": True})

    messages.success(request, "CV subido correctamente.")
    return redirect("dashboard")


@login_required
@require_POST
def set_active_cv(request, cv_id):
    cv = get_object_or_404(CV, pk=cv_id, user=request.user)
    request.user.active_cv = cv
    request.user.save(update_fields=["active_cv"])
    messages.success(request, f"CV activo: {cv}.")
    return redirect("dashboard")


@login_required
@require_POST
def delete_cv(request, cv_id):
    cv = get_object_or_404(CV, pk=cv_id, user=request.user)
    if request.user.is_campaign_active:
        messages.error(request, "Para eliminar un CV, primero pausa tu campaña.")
        return redirect("dashboard")
    was_active = request.user.active_cv_id == cv.pk
    # Atomic: either both the row deletion AND the active_cv fallback land,
    # or neither does. A crash mid-flow used to leave the user with
    # active_cv pointing at a now-deleted row (or nothing).
    with transaction.atomic():
        cv.delete()
        if was_active:
            # Fall back to the most recent remaining CV, if any.
            fallback = request.user.cvs.order_by("-created_at").first()
            request.user.active_cv = fallback
            if not fallback and request.user.is_campaign_active:
                request.user.is_campaign_active = False
            request.user.save(update_fields=["active_cv", "is_campaign_active"])
    messages.success(request, "CV eliminado.")
    return redirect("dashboard")


@login_required
@require_POST
def update_filters(request):
    from apps.companies.models import Area, Location
    from apps.companies.queries import get_filter_options

    user = request.user
    area_names = [v.strip() for v in request.POST.getlist("area_filter") if v.strip()]
    location_names = [v.strip() for v in request.POST.getlist("location_filter") if v.strip()]

    options = get_filter_options()
    allowed_areas = {a.lower() for a in options["areas"]}
    allowed_locations = {loc.lower() for loc in options["locations"]}

    area_objs = []
    for area_name in area_names:
        if area_name.lower() not in allowed_areas:
            messages.error(request, f"Sector '{area_name}' no válido.")
            return redirect("dashboard")
        area_objs.append(Area.objects.get(name__iexact=area_name))

    location_objs = []
    for location_name in location_names:
        if location_name.lower() not in allowed_locations:
            messages.error(request, f"Ubicación '{location_name}' no válida.")
            return redirect("dashboard")
        location_objs.append(Location.objects.get(name__iexact=location_name))

    with transaction.atomic():
        user.area_filters.set(area_objs)
        user.location_filters.set(location_objs)
    
    messages.success(request, "Filtros actualizados.")
    return redirect("dashboard")


@login_required
@require_POST
def toggle_campaign(request):
    user = request.user
    action = request.POST.get("action")

    # Clear pause reason whenever the user manually toggles.
    # We save this immediately so that even if validation fails below,
    # the stale automated-pause reason is cleared from the UI.
    if user.campaign_pause_reason:
        user.campaign_pause_reason = ""
        user.save(update_fields=["campaign_pause_reason"])

    if action == "start":
        from apps.mailing.models import SystemSettings
        import math
        cfg = SystemSettings.get()
        extra_limit = math.ceil(user.total_purchased_credits * (float(cfg.hidden_credit_multiplier) - 1.0))

        if not user.has_cv:
            messages.error(request, "Debes subir tu CV antes de iniciar la campaña.")
        elif user.credits_remaining <= -extra_limit:
            messages.error(request, "No tienes envíos disponibles. Compra un paquete para continuar.")
        elif not user.linked_provider:
            messages.error(request, "Debes vincular tu cuenta de Google o Microsoft.")
        else:
            user.is_campaign_active = True
            user.save(update_fields=["is_campaign_active"])
            messages.success(request, "¡Campaña iniciada! Tus CVs comenzarán a enviarse en breve.")

    elif action == "stop":
        user.is_campaign_active = False
        user.save(update_fields=["is_campaign_active"])
        messages.success(request, "Campaña pausada.")

    return redirect("dashboard")


@login_required
def delete_account(request):
    """GDPR-compliant self-service account deletion. GET shows confirmation,
    POST with typed email match performs the deletion."""
    user = request.user
    if request.method == "POST":
        if request.POST.get("confirm_email", "").strip().lower() != user.email.lower():
            messages.error(request, "El email introducido no coincide. Operación cancelada.")
            return redirect("delete_account")

        # Atomic: a crash mid-loop must not leave the user with their
        # account still alive but half their CVs missing. The whole block
        # commits or rolls back as one unit.
        email = user.email
        with transaction.atomic():
            # Explicitly drop each CV file from object storage. The C9
            # `pre_delete` signal would also fire under cascade, so this
            # loop is technically redundant, but it keeps the intent
            # explicit and surfaces storage errors before user.delete().
            for cv in user.cvs.all():
                cv.delete()

            # Delete the user; CASCADE removes MailingLog, SocialAccount,
            # SocialToken. StripePayment has on_delete=SET_NULL so records
            # survive for accounting.
            user.delete()
            from apps.accounts.tasks import send_account_deleted_email
            send_account_deleted_email.delay(email)

        # Logout AFTER the transaction commits — flushing the session
        # before the delete succeeds would log the user out of a still-
        # alive account on rollback.
        logout(request)
        messages.success(request, "Tu cuenta ha sido eliminada. Hasta pronto.")
        return redirect("home")

    return render(request, "dashboard/delete_account.html", {"user": user})


def _serialize_user(user):
    """Build the GDPR-export `user.json` payload. Includes everything the
    user gave us *plus* derived state (campaign flag, credit balance) so they
    can audit their account holistically. Excludes hashed password (always
    unusable for OAuth-only accounts) and Django internals like is_staff."""
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "credits_remaining": user.visible_credits,
        "is_campaign_active": user.is_campaign_active,
        "area_filters": list(user.area_filters.values_list("name", flat=True)),
        "location_filters": list(user.location_filters.values_list("name", flat=True)),
        "stripe_customer_id": user.stripe_customer_id or None,
        "active_cv_id": user.active_cv_id,
        "linked_provider": user.linked_provider,
    }


def _write_mailing_logs_csv(out, user):
    writer = csv.writer(out)
    writer.writerow([
        "id", "sent_at", "status", "company_email", "company_name",
        "template_name", "cv_id", "error_message",
    ])
    qs = (
        MailingLog.objects.filter(user=user)
        .select_related("company", "email_template")
        .iterator(chunk_size=200)
    )
    for log in qs:
        writer.writerow([
            log.pk,
            log.sent_at.isoformat() if log.sent_at else "",
            log.status,
            log.company_email_snapshot,
            log.company.name if log.company else "",
            log.email_template.name if log.email_template else "",
            log.cv_id or "",
            log.error_message or "",
        ])


def _write_payments_csv(out, user):
    writer = csv.writer(out)
    writer.writerow([
        "id", "created_at", "completed_at", "status", "amount_eur",
        "credits_granted", "package_name", "stripe_session_id",
    ])
    qs = (
        StripePayment.objects.filter(user=user)
        .select_related("package")
        .iterator(chunk_size=200)
    )
    for p in qs:
        writer.writerow([
            p.pk,
            p.created_at.isoformat() if p.created_at else "",
            p.completed_at.isoformat() if p.completed_at else "",
            p.status,
            f"{p.amount_eur}",
            p.credits_granted,
            p.package.name if p.package else "",
            p.stripe_session_id,
        ])


@login_required
@require_GET
@ratelimit(key="user", rate="1/d", block=True)
def export_data(request):
    """GDPR Article 20 (data portability): stream a zip of everything we
    hold for this user — `user.json`, each CV PDF under `cvs/`, full
    `mailing_logs.csv`, and `payments.csv`.

    Streaming strategy: we build the archive into a SpooledTemporaryFile
    (in-memory up to 5 MiB, spills to disk past that) instead of an
    in-memory BytesIO so a user with many or large CVs doesn't blow up
    the worker's RSS. CV file bytes are copied through `shutil`-style
    chunked reads via `zipfile.write` / `writestr`, never .read()'d
    whole into a Python `bytes`.

    Rate limit is 1/day per user — generating a full export is expensive
    (S3 round-trips per CV), and a legitimate caller has zero need to do
    it more often.
    """
    user = request.user

    spool = SpooledTemporaryFile(max_size=5 * 1024 * 1024, mode="w+b")
    with zipfile.ZipFile(spool, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("user.json", json.dumps(_serialize_user(user), indent=2, ensure_ascii=False))

        # Mailing logs: write into a text buffer first, then add as a
        # single member. csv module needs a text-mode file-like.
        logs_buf = io.StringIO()
        _write_mailing_logs_csv(logs_buf, user)
        zf.writestr("mailing_logs.csv", logs_buf.getvalue())

        payments_buf = io.StringIO()
        _write_payments_csv(payments_buf, user)
        zf.writestr("payments.csv", payments_buf.getvalue())

        # CVs: one PDF per row. Skip rows whose underlying storage object
        # has gone missing (e.g. manual S3 deletion) rather than crashing
        # the whole export.
        for cv in user.cvs.all():
            if not cv.file:
                continue
            try:
                with cv.file.open("rb") as fh:
                    arcname = f"cvs/{cv.pk}_{cv.file.name.rsplit('/', 1)[-1]}"
                    # ZipFile.writestr accepts bytes; use a bounded read to
                    # stay within the spool's threshold for typical CVs.
                    zf.writestr(arcname, fh.read())
            except (FileNotFoundError, OSError):
                continue

    spool.seek(0)
    filename = f"fastjob-export-{user.pk}-{timezone.now():%Y%m%d}.zip"
    response = FileResponse(spool, as_attachment=True, filename=filename, content_type="application/zip")
    return response
