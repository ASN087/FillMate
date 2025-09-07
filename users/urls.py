from django.urls import path
from django.shortcuts import render  # Import render function
# Import views correctly
from .views import (
    RegisterView, LoginView, protected_view, user_dashboard, logout_view,
    hod_dashboard, MarkNotificationRead, upload_signature, AdminLoginView,
    login_page_view, signup_page_view, about_view, hod_submission_list # Add new view names
)
from notifications.views import AllNotificationsView # Assuming this exists and is needed
from django.contrib.auth.views import LogoutView as DjangoLogoutView # Default logout if needed
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'users' # Keep app_name for namespacing if needed elsewhere

# API Endpoints (These will be mounted under /api/users/ in the main urls.py)
api_urlpatterns = [
    # URL: /api/users/login/ (Handles POST for authentication)
    path('login/', LoginView.as_view(), name='api_login'),

    # URL: /api/users/register/ (Handles POST for API registration)
    path('register/', RegisterView.as_view(), name='api_register'),

    # URL: /api/users/token/refresh/
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # URL: /api/users/protected/
    path('protected/', protected_view, name='protected_api'),

    # URL: /api/users/notifications/<int:pk>/read/
    path('notifications/<int:pk>/read/', MarkNotificationRead.as_view(), name='mark_notification_read'),
    # Add other API endpoints here
]

# Web/User-Facing URLs (These will be mounted under / or /accounts/ in the main urls.py)
web_urlpatterns = [
    # URL: /login/ (Page displaying the login form - Handles GET)
    path('login-page/', lambda request: render(request, 'login.html', {'is_auth_page': True}), name='login_page'),

    # URL: /signup/ (Page displaying the signup form - Handles GET)
    path('signup/', RegisterView.as_view(), name='signup'),
    # Note: The POST for signup form is handled by RegisterView's non-JSON path,
    # but we need a separate URL for the API endpoint if we want POST /api/users/register/
    # Let's assume the form POSTs to /signup/ for now and RegisterView handles it.
    # OR explicitly handle the form POST:
    path('register/form/', RegisterView.as_view(), name='register_form_post'), # Example if needed

    # URL: /logout/ (Handles POST for logout action)
    path('logout/', logout_view, name='logout'),

    # User Dashboards & Actions (Session protected)
    # URL: /dashboard/
    path('dashboard/', user_dashboard, name='user_dashboard'),
    # URL: /hod-dashboard/
    path('hod-dashboard/', hod_dashboard, name='hod_dashboard'),

    path('hod-dashboard/list/<str:status>/', hod_submission_list, name='hod_submission_list'),
    # URL: /upload-signature/
    path('upload-signature/', upload_signature, name='upload_signature'),

    path('about/', about_view, name='about'),

    # Consider moving notification views here if they are web pages
    # path('notifications/', AllNotificationsView.as_view(), name='all_notifications'), # Example
]

urlpatterns = []

# Combine for inclusion if needed elsewhere, but we'll import lists directly
# urlpatterns = api_urlpatterns + web_urlpatterns