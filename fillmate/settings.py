from pathlib import Path
from datetime import timedelta
import os

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = 'django-insecure-g&^1b^0*5xk3c^40-*r55da6m2v+_4$35*eea^_*bvm464yhr0'
DEBUG = True
ALLOWED_HOSTS = []

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'django_bootstrap5',
    'rest_framework_simplejwt',
    'rest_framework.authtoken',
    #'corsheaders',
    'channels',
     

    # Custom apps
    'users',
    'documents',
    'notifications.apps.NotificationsConfig',
]

# JWT Authentication Settings
SIMPLE_JWT = {
    
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE-REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    # --- REMOVED JWT Cookie specific settings ---
    # We will rely on standard sessions for web and Authorization header for APIs
    # 'AUTH_COOKIE': 'access_token',
    # 'AUTH_COOKIE_SECURE': True, # Handled by SESSION_COOKIE_SECURE for session cookies
    # 'AUTH_COOKIE_SAMESITE': 'Lax', # Handled by SESSION_COOKIE_SAMESITE
    # 'AUTH_COOKIE_REFRESH': 'refresh_token',
}

# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Default to allowing anyone, protect views individually
        'rest_framework.permissions.AllowAny',
    ],
}

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db' # Or cache, etc.
SESSION_COOKIE_NAME = 'sessionid' # Use the standard Django session cookie name
SESSION_COOKIE_AGE = 1209600 # 2 weeks, default
SESSION_SAVE_EVERY_REQUEST = False # Default, saves only on modification
SESSION_EXPIRE_AT_BROWSER_CLOSE = False # Default

# --- Keep Admin separate cookie settings if AdminSessionMiddleware is used ---
# Note: The AdminSessionMiddleware implementation might need review if issues persist
SESSION_COOKIE_ADMIN_NAME = 'admin_sessionid'  # Custom name for admin
SESSION_COOKIE_ADMIN_PATH = '/admin/'  # Restrict admin cookie to /admin/ path

# Security settings for cookies
SESSION_COOKIE_SECURE = False # Set to True in production (HTTPS)
SESSION_COOKIE_HTTPONLY = True # Prevent client-side JS access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax' # Recommended default

CSRF_COOKIE_SECURE = False # Set to True in production (HTTPS)
CSRF_COOKIE_HTTPONLY = False # CSRF token NEEDS to be readable by JS
CSRF_COOKIE_SAMESITE = 'Lax'

# Middleware
MIDDLEWARE = [
    #'corsheaders.middleware.CorsMiddleware',
      # Custom middleware for admin session handling
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'fillmate.middleware.AdminSessionMiddleware', # Keep for admin isolation - place AFTER SessionMiddleware
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Associates user with session
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

# URL Configuration
ROOT_URLCONF = 'fillmate.urls'

# Templates Configuration (✅ Fix: Ensure Django finds templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # ✅ Ensures templates are loaded
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ✅ ADD YOUR CONTEXT PROCESSOR HERE:
                'notifications.context_processors.user_context',
            ],
        },
    },
]

# WSGI Application
WSGI_APPLICATION = 'fillmate.wsgi.application'

# Database Configuration (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'FillMate',
        'USER': 'postgres',
        'PASSWORD': '112233',
        'HOST': 'localhost',  # Use 'localhost' for local development
        'PORT': '5432',

    }
}

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ✅ Static Files Configuration (CSS, JS, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # ✅ Ensures Django serves static files from /static/
]

# ✅ Media Files Configuration (For Uploaded Files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

BOOTSTRAP5 = {
    'theme_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'javascript_url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'css_url': None,  # We're using our custom CSS
}

# Authentication Settings
LOGIN_URL = '/api/users/login/'  # Explicit path to your login
LOGIN_REDIRECT_URL = '/dashboard/' # Default redirect *after* login (can be overridden)
LOGOUT_REDIRECT_URL = 'home'  # Where to redirect after logout

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'documents': {  # Your app name
            'handlers': ['console'],
            'level': 'DEBUG',  # More detailed logs for your app
            'propagate': False,
        },
        'users': { 'handlers': ['console'], 'level': 'DEBUG', 'propagate': False, }, # Add logger for users app
    },
}

# Add this at the bottom of settings.py
SIMPLE_NOTIFICATION_SETTINGS = {
    'USE_WEBSOCKETS': False,  # Set to True if you want real-time updates
    'DEFAULT_EXPIRY_DAYS': 30,
    'receive_handler_path': 'custom_module.custom_py_file.custom_receive_handler',
}

