import logging

from django.http import HttpResponseBadRequest, JsonResponse
from django.template import TemplateDoesNotExist, loader

logger = logging.getLogger(__name__)


def _is_xhr(request):
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )


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
