from django import template
from django.conf import settings

register = template.Library()

@register.filter
def get_poster_url(poster_path):
    """Process poster paths to return the correct URL format."""
    if not poster_path:
        return None
    if poster_path.startswith('posters/'):
        return f"{settings.MEDIA_URL}{poster_path}"
    if poster_path.startswith(('http://', 'https://')):
        return poster_path
    return f"https://image.tmdb.org/t/p/w500{poster_path}" 