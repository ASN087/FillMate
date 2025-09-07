from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout # Alias login to avoid conflict
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User, Group
from .serializers import RegisterSerializer, LoginSerializer, JWTSerializer, UserSerializer
from documents.models import SubmittedDocument  # Import the SubmittedDocument model
from rest_framework.decorators import api_view, permission_classes
from django.urls import reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie # Use ensure_csrf_cookie for templates
from django.views.generic import ListView
from django.views.decorators.http import require_http_methods
import json
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.views import LoginView as DjangoAuthLoginView
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from datetime import timedelta
from notifications.models import Notification
from .forms import SignatureUploadForm  # Import SignatureUploadForm
from .models import UserProfile  # Import UserProfile model



class MarkNotificationRead(APIView):

    permission_classes = [IsAuthenticated] # Ensure only logged-in users can mark read
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})



# ✅ User Registration View
class RegisterView(APIView):
    """Handles both API and form-based registration"""

    permission_classes = [AllowAny] # Anyone can access registration
    
    def get(self, request):
        """Show registration form"""
        return render(request, 'signup.html', {'is_auth_page': True})
    
    def post(self, request):
        """Handle registration"""
        if request.content_type == 'application/json':
            # API request
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Form submission
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password') # Get confirm password

            if password != confirm_password:
                 messages.error(request, "Passwords do not match.")
                 return redirect('users:signup') # Redirect back to signup form
            
            # Basic validation (consider using a Django Form)
            if not username or not email or not password:
                 messages.error(request, "Please fill in all fields.")
                 return redirect('users:signup')

            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' is already taken.")
                return redirect('users:signup')

            if User.objects.filter(email=email).exists():
                 messages.error(request, f"Email '{email}' is already registered.")
                 return redirect('users:signup')
            
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                messages.success(request, "Account created successfully! Please login.")
                return redirect('users:login_page') # Redirect to login page
            except Exception as e:
                print(f"Error creating user: {e}")
                messages.error(request, f"An unexpected error occurred. Please try again.")
                return redirect('users:signup')
            



class AdminLoginView(DjangoAuthLoginView):
    template_name = 'admin/login.html'

    '''def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.delete_cookie('regular_sessionid')
        response.delete_cookie('hod_sessionid')
        response.delete_cookie('access_token')
        return response
    
    def dispatch(self, request, *args, **kwargs):
        # Clear any existing authentication
        request.session.flush()
        response = super().dispatch(request, *args, **kwargs)
        
        # Clear all conflicting cookies
        response.delete_cookie('regular_sessionid')
        response.delete_cookie('hod_sessionid')
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response'''
    
    def form_valid(self, form):
        # Default behavior - logs the user in using standard session
        auth_login(self.request, form.get_user())

        # Set the specific admin session cookie
        admin_session_key = self.request.session.session_key
        response = HttpResponseRedirect(self.get_success_url()) # Default is /admin/
        
        # Set the admin-specific cookie
        response.set_cookie(
            settings.SESSION_COOKIE_ADMIN_NAME, # Use the name from settings
            admin_session_key,
            path=settings.SESSION_COOKIE_ADMIN_PATH, # Use the path from settings
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            samesite=settings.SESSION_COOKIE_SAMESITE
        )
        # Mark this session as an 'admin' session for AdminSessionMiddleware
        self.request.session['is_admin'] = True
        self.request.session.save() # Ensure session is saved

        # Clear regular session cookie if present
        if settings.SESSION_COOKIE_NAME in self.request.COOKIES:
            response.delete_cookie(settings.SESSION_COOKIE_NAME, path='/')

        return response
    

# ✅ User Login View
class LoginView(APIView):

    """Handles POST requests for login (both API and Form)."""
    permission_classes = [AllowAny] # Anyone can attempt to login

    # GET request is handled by login_page view now
    # def get(self, request):
    #     return redirect(reverse('users:login_page') + f"?next={request.GET.get('next', '/')}")


    def post(self, request):
        """Handle login attempts"""
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # --- User authenticated successfully ---
            auth_login(request, user) # Establish the standard Django session

             # ✅ *** CLEAR ANY OLD MESSAGES *** ✅
            storage = messages.get_messages(request)
            for message in storage:
                pass # Iterate through storage to mark messages as seen
            storage.used = True # Explicitly mark as used

            # Check if the user is admin/staff
            if user.is_staff:
                # For staff users, primarily rely on the admin login flow (/admin/login/)
                # which sets the admin-specific cookie.
                # Redirect them towards the admin interface.
                # Don't generate JWTs for admin interface access.
                # Optionally set the admin cookie here if logging in via the *main* login form
                admin_session_key = request.session.session_key
                request.session['is_admin'] = True # Mark session for middleware
                request.session.save()

                response = JsonResponse({'redirect_url': '/admin/'}) # Send redirect URL for JS

                # Set admin cookie (might be redundant if AdminLoginView/Middleware handles it)
                response.set_cookie(
                    settings.SESSION_COOKIE_ADMIN_NAME,
                    admin_session_key,
                    path=settings.SESSION_COOKIE_ADMIN_PATH,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE
                )
                 # Clear regular session cookie just set by auth_login
                # response.delete_cookie(settings.SESSION_COOKIE_NAME, path='/') # Careful: This might log them out immediately if admin middleware fails

                return response

            # --- Regular user or HOD ---
            else:
                # Generate JWT tokens for API usage by the frontend JS
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Determine redirect URL based on role (HOD or regular)
                redirect_url = self.get_redirect_url(user)

                response = JsonResponse({
                    'redirect_url': redirect_url,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': UserSerializer(user).data # Send user data if needed by frontend
                })

                # Standard session cookie ('sessionid') is already set by auth_login()
                # Optionally set JWTs as HttpOnly cookies if needed elsewhere,
                # but frontend JS primarily uses tokens from JSON response/localStorage
                # response.set_cookie(
                #     'access_token', access_token, httponly=True, samesite='Lax', secure=settings.SESSION_COOKIE_SECURE, max_age=...
                # )
                # response.set_cookie(
                #     'refresh_token', refresh_token, httponly=True, samesite='Lax', secure=settings.SESSION_COOKIE_SECURE, max_age=...
                # )

                return response
        else:
            # --- Authentication failed ---
            return JsonResponse({'error': 'Invalid Username or Password'}, status=status.HTTP_401_UNAUTHORIZED)

    def get_redirect_url(self, user):
        """Determine redirect URL based on user role"""
        # Check if user is in the 'HOD' group (ensure group 'HOD' exists)
        try:
             # Check group membership safely
            if user.groups.filter(name="HOD").exists():
                return reverse('users:hod_dashboard') # Use reverse for safety
        except Group.DoesNotExist:
             print("Warning: 'HOD' group does not exist.") # Log warning if group missing
             pass # Fall through to default dashboard
        except AttributeError:
             # Handle cases where user object might not have 'groups' (e.g., AnonymousUser)
             pass

        return reverse('users:user_dashboard') # Default redirect
    

# Function-based view to render the login page template
@ensure_csrf_cookie # Ensure CSRF cookie is set for the form
def login_page_view(request):
    # Redirect if already logged in? Optional.
    # if request.user.is_authenticated and not request.user.is_staff:
    #      # Determine redirect based on role if already logged in
    #      if request.user.groups.filter(name="HOD").exists():
    #          return redirect('users:hod_dashboard')
    #      else:
    #          return redirect('users:user_dashboard')
    # elif request.user.is_authenticated and request.user.is_staff:
    #      return redirect('/admin/')

    return render(request, 'login.html')

    
# User Dashboard View (Session protected)
@login_required # Requires standard session login
def user_dashboard(request):
    """User Dashboard View (Renders userdash.html)"""
    # Redirect staff users away from the regular dashboard
    if request.user.is_staff:
        return redirect('/admin/')
    # Redirect HOD users to their specific dashboard
    if request.user.groups.filter(name='HOD').exists():
         return redirect('users:hod_dashboard')

    # Fetch notifications for the specific user
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10] # Get recent 10

    context = {
        'user': request.user,
        'notifications': notifications,
        # Add any other context needed for userdash.html
    }
    return render(request, 'userdash.html', context)



def is_hod(user):
    """Check if the user is authenticated and in the HOD group."""
    return user.is_authenticated and user.groups.filter(name='HOD').exists()

@login_required
@user_passes_test(is_hod, login_url='/dashboard/') # Redirect non-HODs to regular dashboard
def hod_dashboard(request):
    """HOD Dashboard View (Renders hoddash.html)"""
    # Get unread notifications
    notifications = Notification.objects.filter(
        recipient=request.user, # Changed from user=request.user
        is_read=False
    ).order_by('-created_at')

    # Get recent submissions (last 7 days)
    recent_submissions = SubmittedDocument.objects.filter(
        # Optional: Filter by status if needed (e.g., only Pending)
        # status='Pending',
        # Optional: Filter by date range
        submitted_at__gte=timezone.now()-timedelta(days=7) # Example: Last 7 days
    ).select_related(
        'user', 'template' # Efficiently fetch related user and template
    ).order_by(
        '-submitted_at' # Order by newest first
    )[:5] # <-- SLICE to get the 5 most recent

    context = {
        'user': request.user,
        'is_hod': True, # Flag for template
        'notifications': notifications,
        'recent_submissions': recent_submissions,
        'pending_count': SubmittedDocument.objects.filter(status='Pending').count(),
        'approved_count': SubmittedDocument.objects.filter(status='Approved').count(),
        'rejected_count': SubmittedDocument.objects.filter(status='Rejected').count(),
    }
    return render(request, 'hoddash.html', context)

# Protected API Endpoint Example (JWT or Session protected)
@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Requires JWT or Session auth via DRF settings
def protected_view(request):
    """A test API endpoint accessible only to authenticated users."""
    return Response({"message": "You are authenticated!", "user": request.user.username})



# Logout View (Handles POST request)
@require_http_methods(["POST"])
def logout_view(request):
    """Logs the user out, clears session and relevant cookies."""
    user_was_staff = request.user.is_staff # Check before logout
    logout(request) # Clears session data and logs out

    response = JsonResponse({"success": True, "redirect_url": reverse("home")}) # Redirect to home after logout

    # Explicitly delete cookies on logout for robustness
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path='/')
    response.delete_cookie(settings.SESSION_COOKIE_ADMIN_NAME, path=settings.SESSION_COOKIE_ADMIN_PATH)
    response.delete_cookie('csrftoken', path='/') # Clear CSRF token as well
    # Clear JWT tokens from cookies if they were set (though primarily using localStorage now)
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/')
    # Also instruct frontend to clear localStorage
    # The JS calling this logout endpoint should clear localStorage

    messages.info(request, "You have been logged out.") # Optional message
    return response


# Admin Logout View (Specific for /admin/logout/)
# Using POST is generally better for logout
@require_http_methods(["POST", "GET"]) # Allow GET for simple links in admin templates
@login_required # Ensure user is logged in before logging out
def admin_logout(request):
    """Logs out an admin user and redirects to admin login."""
    admin_cookie_name = getattr(settings, 'SESSION_COOKIE_ADMIN_NAME', 'admin_sessionid')
    admin_cookie_path = getattr(settings, 'SESSION_COOKIE_ADMIN_PATH', '/admin/')
    logout(request) # Django's logout handles session clearing

    # Redirect to admin login page
    response = HttpResponseRedirect('/admin/login/') # Use reverse('admin:login') if possible

    # Explicitly delete the admin cookie
    response.delete_cookie(admin_cookie_name, path=admin_cookie_path)
    # Also delete the standard session cookie if it somehow exists
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path='/')
    response.delete_cookie('csrftoken', path='/')

    messages.info(request, "You have been successfully logged out.")
    return response


# Signup Page View (Renders form) - Renamed from signup_view for clarity
@ensure_csrf_cookie
def signup_page_view(request):
     # Redirect if already logged in?
    if request.user.is_authenticated:
        return redirect('users:user_dashboard') # Or home?
    return render(request, 'signup.html', {'is_auth_page': True})
@login_required
def upload_signature(request):
    # ✅ Get or create the profile for the logged-in user
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Use the existing profile instance
        form = SignatureUploadForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # The form is already linked to the profile instance
            updated_profile = form.save(commit=False)
            # Only set the timestamp if the signature field actually changed and has a value
            if 'digital_signature' in form.changed_data and updated_profile.digital_signature:
                 updated_profile.signature_uploaded_at = timezone.now()
            updated_profile.save()
            messages.success(request, "Signature uploaded successfully!") # Add feedback

            # Redirect based on role (assuming HOD uploads signature from their dash)
            if request.user.groups.filter(name='HOD').exists():
                 return redirect('users:hod_dashboard')
            else:
                 # Or redirect to a general profile page if needed
                 return redirect('users:user_dashboard') # Adjust as needed
        else:
             # Add specific form errors if possible
             error_message = "Error uploading signature. Please check the file."
             if form.errors:
                 error_message += " " + str(form.errors.get('digital_signature', '')) # Show specific error
             messages.error(request, error_message)
    else:
        # Pass the existing profile instance to the form
        form = SignatureUploadForm(instance=profile)

    # Pass the profile object to the template (optional, but can be useful)
    return render(request, 'upload_signature.html', {'form': form, 'profile': profile})

def about_view(request):
    return render(request, 'about.html')


@login_required
@user_passes_test(is_hod)
def hod_submission_list(request, status):
    """
    Displays a list of submissions filtered by status for HODs.
    Handles 'pending', 'approved', 'rejected'.
    """
    valid_statuses = ['pending', 'approved', 'rejected']
    status_filter = status.lower() # Ensure lowercase comparison

    if status_filter not in valid_statuses:
        # Redirect to main HOD dash if status is invalid
        return redirect('users:hod_dashboard')

    # Capitalize status for DB query ('Pending', 'Approved', 'Rejected')
    status_db = status_filter.capitalize()

    # Query submissions based on status
    submission_list = SubmittedDocument.objects.filter(
        status=status_db
    ).select_related(
        'user', 'template', 'approved_version' # Include approved_version here
    ).order_by('-submitted_at')

    # Pagination
    paginator = Paginator(submission_list, 15) # Show 15 submissions per page
    page_number = request.GET.get('page')
    try:
        submissions = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        submissions = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        submissions = paginator.page(paginator.num_pages)

    context = {
        'submissions': submissions, # Paginated submissions
        'status': status_db, # Pass the capitalized status for title/logic
        'page_title': f"{status_db} Submissions",
        'is_paginated': paginator.num_pages > 1, # Pass flag for template
        'page_obj': submissions, # Pass page object for pagination controls
    }
    return render(request, 'hod_submission_list.html', context)


