from .models import WatchlistItem
from django.conf import settings

def watchlist_processor(request):
    if request.user.is_authenticated:
        watchlist_items = WatchlistItem.objects.filter(user=request.user).order_by('-added_date')
    else:
        watchlist_items = []
    return {'watchlist_items': watchlist_items}
def media_url(request):
    return {'MEDIA_URL': settings.MEDIA_URL}