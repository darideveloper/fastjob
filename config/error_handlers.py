import logging

from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.template import TemplateDoesNotExist, loader

logger = logging.getLogger(__name__)


def _is_xhr(request):
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )


def handler404(request, exception, template_name="404.html"):
    logger.warning("404 Not Found at %s", request.path)

    if _is_xhr(request):
        return JsonResponse(
            {"error": "El recurso solicitado no existe."}, status=404
        )

    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseNotFound(
            "<h1>Not Found (404)</h1>",
            content_type="text/html; charset=utf-8",
        )
    return HttpResponseNotFound(template.render(request=request))


def handler500(request, template_name="500.html"):
    logger.error("500 Internal Server Error at %s", request.path)

    if _is_xhr(request):
        return JsonResponse(
            {"error": "Error interno del servidor."}, status=500
        )

    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError(
            "<h1>Internal Server Error (500)</h1>",
            content_type="text/html; charset=utf-8",
        )
    return HttpResponseServerError(template.render(request=request))


def handler400(request, exception, template_name="400.html"):
    # Replaces django.views.defaults.bad_request so:
    # - The originating exception class+message is logged (Django's default
    #   only logs "Bad Request: <path>", which leaves operators blind to
    #   parser errors raised in middleware before any view runs).
    # - XHR clients get a JSON body with the real diagnostic, instead of an
    #   opaque HTML page that their JSON.parse fallback can't decode.
    exc_class = type(exception).__name__ if exception else "Unknown"
    exc_message = str(exception) if exception else ""
    logger.warning(
        "400 Bad Request at %s: %s: %s",
        request.path,
        exc_class,
        exc_message,
    )

    if _is_xhr(request):
        diagnostic = (
            f"Solicitud inválida ({exc_class}): {exc_message}"
            if exc_message
            else f"Solicitud inválida ({exc_class})."
        )
        return JsonResponse({"error": diagnostic}, status=400)

    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseBadRequest(
            "<h1>Bad Request (400)</h1>",
            content_type="text/html; charset=utf-8",
        )
    return HttpResponseBadRequest(
        template.render(request=request, context={"exception": str(exception)})
    )
