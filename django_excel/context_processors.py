"""Template context processors for the django_excel project."""
from django.utils import timezone

from django_excel import __version__


def app_meta(request):
    """Expose the app version and current year to every template (used by the page footer)."""
    return {
        "app_version": __version__,
        "current_year": timezone.now().year,
    }
