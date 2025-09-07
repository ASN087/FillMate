# notifications/context_processors.py
from .models import Notification



def user_context(request):
    context = {}
    if request.user.is_authenticated:
        # --- Existing Notification Logic ---
        unread_notifications_qs = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )
        context['unread_notifications'] = unread_notifications_qs.order_by('-created_at')[:10]
        context['unread_count'] = unread_notifications_qs.count() # Count efficiently

        # --- ADD HOD Check ---
        try:
            # Check if the user is in the 'HOD' group
            context['is_hod_user'] = request.user.groups.filter(name='HOD').exists()
        except AttributeError:
             # Handle AnonymousUser or other cases where 'groups' might not exist
             context['is_hod_user'] = False
    else:
        context['unread_notifications'] = []
        context['unread_count'] = 0
        context['is_hod_user'] = False

    return context