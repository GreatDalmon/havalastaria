from django.db.models import Q
from .models import Message


def unread(request):
    """Adds {{ unread_count }} (messages waiting for this user) to every template."""
    if not request.user.is_authenticated:
        return {}
    n = (Message.objects.filter(is_read=False)
         .filter(Q(conversation__client=request.user) | Q(conversation__agent__user=request.user))
         .exclude(sender=request.user).count())
    return {'unread_count': n}
