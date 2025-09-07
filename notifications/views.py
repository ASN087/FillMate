from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from .models import Notification

def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    # Redirect to the document if linked, or to a default URL
    if notification.content_object:
        return redirect(f'/documents/{notification.object_id}/')
    return redirect(notification.content_object.get_absolute_url() if hasattr(notification.content_object, 'get_absolute_url') else '/hod-dashboard/')

class AllNotificationsView(ListView):
    template_name = 'all_notifications.html'
    context_object_name = 'notifications'
    paginate_by = 10
    
    def get_queryset(self):
        # Get all notifications for the current user (as recipient)
        queryset = Notification.objects.filter(
            recipient=self.request.user
        ).select_related(
            'sender',  # Optimize by fetching related sender data
            'recipient'
        ).order_by('-created_at')
        
        # Optional: Add filter for read/unread status
        if self.request.GET.get('filter') == 'unread':
            queryset = queryset.filter(is_read=False)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data
        context['unread_count'] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        return context