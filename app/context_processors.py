from django.conf import settings


def branding(_request):
    return {
        "site_name": settings.SITE_NAME,
        "site_short_name": settings.SITE_SHORT_NAME,
        "site_footer_name": settings.SITE_FOOTER_NAME,
        "site_footer_url": settings.SITE_FOOTER_URL,
    }
