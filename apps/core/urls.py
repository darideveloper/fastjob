from django.conf import settings
from django.urls import reverse


def abs_url(viewname, *args, **kwargs):
    """Return a fully qualified absolute URL for a registered Django view.

    Wraps :func:`django.urls.reverse` and prefixes the result with the
    configured site scheme and domain (``SITE_SCHEME`` + ``SITE_DOMAIN``).
    Raises ``NoReverseMatch`` if ``viewname`` is not a registered URL name,
    so typos surface immediately instead of silently shipping a broken link
    in an email.
    """
    path = reverse(viewname, args=args, kwargs=kwargs)
    return f"{settings.SITE_SCHEME}://{settings.SITE_DOMAIN}{path}"
