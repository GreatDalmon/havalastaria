import re
from django import template

register = template.Library()


@register.filter
def display_name(user):
    """Full name if set, otherwise 'john.adeyemi' -> 'John Adeyemi'."""
    if not user:
        return ""
    full = (user.get_full_name() or "").strip()
    if full:
        return full
    raw = getattr(user, "username", "") or str(user)
    return " ".join(w.capitalize() for w in re.split(r"[._\-\s]+", raw) if w)
