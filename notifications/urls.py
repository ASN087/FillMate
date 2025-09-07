from django.urls import path
from .views import mark_notification_read, AllNotificationsView

app_name = 'notifications'

urlpatterns = [
    path('<int:pk>/read/', mark_notification_read, name='mark_read'),
    path('', AllNotificationsView.as_view(), name='all-notifications'),
]