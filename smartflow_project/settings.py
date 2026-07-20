# smartflow_project/settings.py
import os
import pathlib
from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as messages_constants

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
# SECURITY
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']

# ─────────────────────────────────────────────
# INSTALLED APPS
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',  
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',  
    'registry',
]

# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartflow_project.urls'

# ─────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'registry.context_processors.notification_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartflow_project.wsgi.application'

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─────────────────────────────────────────────
# CUSTOM USER MODEL
# ─────────────────────────────────────────────
AUTH_USER_MODEL = 'registry.User'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ─────────────────────────────────────────────
# PASSWORD VALIDATION
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────
# LOCALISATION
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Harare'
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────
# STATIC & MEDIA FILES
# ─────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'registry' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'SmartFlow <noreply@smartflow.com>'

# ─────────────────────────────────────────────
# MESSAGES 
# ─────────────────────────────────────────────
MESSAGE_TAGS = {
    messages_constants.DEBUG:   'alert-secondary',
    messages_constants.INFO:    'alert-info',
    messages_constants.SUCCESS: 'alert-success',
    messages_constants.WARNING: 'alert-warning',
    messages_constants.ERROR:   'alert-danger',
}

# ─────────────────────────────────────────────
# SMARTFLOW AI CONFIGURATION (Google Gemini)
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')
AI_MODEL = os.getenv('AI_MODEL', 'gemini-2.5-flash')
AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', 2000))
AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', 0.7))

# AI Feature Flags
AI_ENABLED = True
AI_SUMMARIZATION_ENABLED = True
AI_GRAMMAR_CHECK_ENABLED = True
AI_FEEDBACK_ENABLED = True
AI_CHATBOT_ENABLED = True
AI_ANALYTICS_ENABLED = True

print(f"🤖 AI Provider: {AI_PROVIDER}")
print(f"🤖 AI Model: {AI_MODEL}")
if GEMINI_API_KEY:
    print("✅ Gemini API Key loaded successfully!")
else:
    print("⚠️ GEMINI_API_KEY not found in .env file!")

# ─────────────────────────────────────────────
# CHANNELS / WEBSOCKET CONFIGURATION
# ─────────────────────────────────────────────
ASGI_APPLICATION = 'smartflow_project.asgi.application'


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}