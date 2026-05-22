import logging

from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited

from apps.core.ratelimit import get_client_ip

logger = logging.getLogger(__name__)


class RatelimitMiddleware:
    """
    Converts the django-ratelimit Ratelimited exception into a proper HTTP 429.
    The library's default returns 403, which confuses CDNs and monitoring tools
    because 403 means "authenticated but forbidden," not "throttled."
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            # Surface throttling events: with no server logs this was
            # previously invisible. WARNING reaches Sentry as a breadcrumb
            # and the console log, making the next incident diagnosable.
            logger.warning(
                "ratelimit: throttled path=%s ip=%s",
                request.path,
                get_client_ip(request),
            )
            return HttpResponse(
                "Demasiadas peticiones. Intenta de nuevo más tarde.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
        return None
