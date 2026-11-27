from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(role):
    """Logged-in users only; users with a different role are sent to their own dashboard."""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.profile.role != role:
                messages.error(request, 'You do not have access to that page.')
                return redirect('dashboard')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
