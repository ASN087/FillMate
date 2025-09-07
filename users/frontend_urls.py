from django.urls import path
from .views import user_dashboard, hod_dashboard

urlpatterns = [
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('hod-dashboard/', hod_dashboard, name='hod_dashboard'),
    # Add other frontend URLs here
]