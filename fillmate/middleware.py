from django.contrib.sessions.backends.db import SessionStore

from django.contrib.auth.models import Group, AnonymousUser, User
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponseRedirect
from django.conf import settings

# Keep AdminSessionMiddleware if you need strict session isolation for /admin/
class AdminSessionMiddleware:
    """
    Ensures only authenticated staff users with the correct admin session
    can access /admin/ paths (except /admin/login/).
    Relies on 'admin_sessionid' cookie set by AdminLoginView or custom LoginView.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_cookie_name = getattr(settings, 'SESSION_COOKIE_ADMIN_NAME', 'admin_sessionid')
        self.admin_cookie_path = getattr(settings, 'SESSION_COOKIE_ADMIN_PATH', '/admin/')
        self.login_url = '/admin/login/' # Consider using reverse('admin:login') if urls are namespaced

    def __call__(self, request):
        # Only process requests for the admin path
        if not request.path.startswith(self.admin_cookie_path):
            return self.get_response(request)

        # Allow access to the admin login page
        if request.path == self.login_url:
            # Clear potentially conflicting non-admin session cookies if present
            response = self.get_response(request)
            if settings.SESSION_COOKIE_NAME in request.COOKIES:
                 response.delete_cookie(settings.SESSION_COOKIE_NAME, path='/') # Clear regular session
            # Clear any old JWT cookies just in case
            if 'access_token' in request.COOKIES:
                response.delete_cookie('access_token', path='/')
            if 'refresh_token' in request.COOKIES:
                response.delete_cookie('refresh_token', path='/')
            return response

        # Try to authenticate using the admin session cookie
        admin_session_key = request.COOKIES.get(self.admin_cookie_name)
        if admin_session_key:
            try:
                admin_session = SessionStore(session_key=admin_session_key)
                user_id = admin_session.get('_auth_user_id')
                # Check if session is considered 'admin' (set during login)
                # and if the user ID exists
                if user_id and admin_session.get('is_admin'): # 'is_admin' flag set in AdminLoginView
                    user = User.objects.get(pk=user_id)
                    # Attach user to request ONLY if they are staff
                    if user.is_staff:
                        request.user = user
                        request.session = admin_session # Use the admin session
                    else:
                         # User is not staff, treat as anonymous for admin path
                        request.user = AnonymousUser()
                else:
                     # Invalid or expired admin session
                    request.user = AnonymousUser()
            except (SessionStore.DoesNotExist, User.DoesNotExist):
                request.user = AnonymousUser()
        else:
            # No admin session cookie
            request.user = AnonymousUser()


        # If after processing, the user is not authenticated staff, redirect to admin login
        # This relies on AuthenticationMiddleware potentially overriding request.user if standard session is also present
        # Re-check authentication status before generating response
        is_authenticated_staff = hasattr(request, 'user') and request.user.is_authenticated and request.user.is_staff

        response = self.get_response(request)

        # Final check: If accessing admin path (not login) and not authenticated staff, redirect.
        if not request.path.startswith(self.login_url) and not is_authenticated_staff:
             # If response isn't already a redirect (e.g., from another middleware)
            if not isinstance(response, HttpResponseRedirect):
                # Clear potentially invalid admin cookie and redirect
                response = HttpResponseRedirect(self.login_url)
                response.delete_cookie(self.admin_cookie_name, path=self.admin_cookie_path)
        elif is_authenticated_staff and admin_session_key:
             # Ensure the correct admin cookie is set/maintained if user is staff
             # This might be redundant if session handling works correctly, but adds robustness
             response.set_cookie(
                 self.admin_cookie_name,
                 admin_session_key,
                 path=self.admin_cookie_path,
                 secure=settings.SESSION_COOKIE_SECURE,
                 httponly=settings.SESSION_COOKIE_HTTPONLY,
                 samesite=settings.SESSION_COOKIE_SAMESITE
             )


        return response


# --- REMOVED JWTCookieMiddleware ---
# Rely on JWTAuthentication in DRF settings for APIs


# --- REMOVED CustomSessionMiddleware ---
# Rely on standard SessionMiddleware

