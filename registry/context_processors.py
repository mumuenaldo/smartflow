# registry/context_processors.py
from django.conf import settings
from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread': unread}
    return {'unread': 0}

def site_url(request):
    return {
        'SITE_URL': settings.SITE_URL,
    }