from django.http import HttpResponse
from django_ratelimit.exceptions import Ratelimited


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
            return HttpResponse(
                "Demasiadas peticiones. Intenta de nuevo más tarde.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
        return None
