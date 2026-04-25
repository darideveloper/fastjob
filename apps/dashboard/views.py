from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import CV
from apps.mailing.models import MailingLog


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
    }
    return render(request, "dashboard/index.html", context)


@login_required
@require_POST
def upload_cv(request):
    cv_file = request.FILES.get("cv_file")
    if not cv_file:
        messages.error(request, "Por favor selecciona un archivo PDF.")
        return redirect("dashboard")

    if not cv_file.name.lower().endswith(".pdf"):
        messages.error(request, "Solo se permiten archivos PDF.")
        return redirect("dashboard")

    if cv_file.size > 10 * 1024 * 1024:
        messages.error(request, "El archivo no puede superar los 10 MB.")
        return redirect("dashboard")

    user = request.user
    label = (request.POST.get("name") or "").strip()[:200]

    # Atomic: create the new CV first, then point active_cv at it. The old CV
    # row is preserved — users can delete it manually if desired — so an upload
    # failure never leaves the user without a CV.
    cv = CV.objects.create(user=user, file=cv_file, name=label)
    user.active_cv = cv
    user.save(update_fields=["active_cv"])
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
    was_active = request.user.active_cv_id == cv.pk
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
    user = request.user
    user.area_filter = request.POST.get("area_filter", "").strip()
    user.location_filter = request.POST.get("location_filter", "").strip()
    user.save(update_fields=["area_filter", "location_filter"])
    messages.success(request, "Filtros actualizados.")
    return redirect("dashboard")


@login_required
@require_POST
def toggle_campaign(request):
    user = request.user
    action = request.POST.get("action")

    if action == "start":
        if not user.has_cv:
            messages.error(request, "Debes subir tu CV antes de iniciar la campaña.")
        elif user.credits_remaining <= 0:
            messages.error(request, "No tienes créditos disponibles. Compra un paquete para continuar.")
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

        # Explicitly drop each CV file from object storage — SET_NULL on
        # MailingLog.cv wouldn't trigger the overridden delete().
        for cv in user.cvs.all():
            cv.delete()

        # Delete the user; CASCADE removes MailingLog, SocialAccount,
        # SocialToken. StripePayment has on_delete=SET_NULL so records
        # survive for accounting.
        logout(request)
        user.delete()
        messages.success(request, "Tu cuenta ha sido eliminada. Hasta pronto.")
        return redirect("home")

    return render(request, "dashboard/delete_account.html", {"user": user})
