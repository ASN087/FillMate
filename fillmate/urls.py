"""
URL configuration for fillmate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.shortcuts import redirect
from users.views import admin_logout

# Import the separated URL patterns from users app
from users.urls import api_urlpatterns as users_api_urls
from users.urls import web_urlpatterns as users_web_urls


# ✅ Function to render index.html
def home(request):
    return render(request, 'index.html')  # Ensure 'index.html' is inside 'templates/'

urlpatterns = [
    # Admin Interface (uses its own auth)
    path('admin/logout/', admin_logout, name='admin_logout'), # Custom admin logout URL
    path('admin/', admin.site.urls), # Standard admin URLs

    #path('', include('users.urls')),  # Frontend URLs at root level
     # Homepage
    path('', home, name='home'),

    # API Endpoints (Grouped under /api/)
    path('api/users/', include((users_api_urls, 'users'), namespace='api_users')), # Include API urls
   # path('api/documents/', include('documents.urls', namespace='api_documents')),
   # path('api/notifications/', include('notifications.urls', namespace='api_notifications')),
    path('api/documents/', include('documents.urls')),
    path('api/notifications/', include('notifications.urls')),
    

    # User Accounts & Web Views (Grouped under /accounts/ for clarity)
    # Include only the web part of users.urls or define them directly here
    # Let's redefine them here for clarity, assuming users/urls.py exports web_urlpatterns
    # path('accounts/', include(users.urls.web_urlpatterns, namespace='accounts')), # Needs adjustment in users/urls.py

    # OR, define explicitly here (simpler if few URLs):
    #path('accounts/', include('users.urls', namespace='users')), # Include ALL users.urls under /accounts/
                                                                   # Requires adjusting users/urls.py to have ONLY web URLs
                                                                   # or using the include tuple method correctly.

    # Let's try including the whole 'users' app under a namespace,
    # but remember API paths are also defined in users/urls.py.
    # This might lead to URLs like /accounts/api/users/login which is not ideal.

    # --- RECOMMENDED STRUCTURE ---
    # Keep API under /api/, keep web under root or /accounts/
    # Adjust users/urls.py to only contain WEB views if mounting here:
    # path('accounts/', include('users.urls', namespace='users')),

    # --- ALTERNATIVE: Keep users/urls.py as combined ---
    # Mount API parts under /api/ and web parts under root or /accounts/
    # path('api/users/', include( (users_api_urls, 'users_api'), namespace='users_api')), # Requires splitting users/urls.py
    # path('accounts/', include( (users_web_urls, 'users_web'), namespace='users')), # Requires splitting users/urls.py

    # --- SIMPLEST START: Include combined users.urls at root ---
    # This means URLs like /login/, /dashboard/, /api/users/login/ all exist
    path('', include((users_web_urls, 'users'), namespace='users')), # Include Web urls
    
    
    
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
