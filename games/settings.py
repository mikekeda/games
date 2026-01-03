"""
Django settings for games project.
"""

import os
import requests
from django.utils.log import DEFAULT_LOGGING as LOGGING

SITE_ENV_PREFIX = "GAMES"


def get_env_var(name, default=""):
    """Get all sensitive data from google vm custom metadata."""
    try:
        name = "_".join([SITE_ENV_PREFIX, name])
        res = os.environ.get(name)
        if res:
            # Check env variable (Jenkins build).
            return res
        else:
            res = requests.get(
                "http://metadata.google.internal/computeMetadata/"
                f"v1/instance/attributes/{name}",
                headers={"Metadata-Flavor": "Google"},
            )
            if res.status_code == 200:
                return res.text
    except requests.exceptions.ConnectionError:
        return default
    return default


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_var(
    "SECRET_KEY", "k&ch)fg&+odbx*#9f66u053$*y1ya9j*s(3!_vk$ix&xvh+_-v"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(get_env_var("DEBUG", "True"))

INTERNAL_IPS = ("127.0.0.1",)

ALLOWED_HOSTS = get_env_var("ALLOWED_HOSTS", "*").split(",")

ADMINS = [("Mike", "mriynuk@gmail.com")]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "channels",
    "social_django",
    "widget_tweaks",
    "core",
]

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar", "django_jenkins"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

if DEBUG:
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

AUTHENTICATION_BACKENDS = (
    "social_core.backends.facebook.FacebookOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

ROOT_URLCONF = "games.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "games.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": get_env_var("DB_NAME", "games"),
        "USER": get_env_var("DB_USER", "games_admin"),
        "PASSWORD": get_env_var("DB_PASSWORD", "games_local_pass"),
        "HOST": get_env_var("DB_HOST", "127.0.0.1"),
        "PORT": "",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# CELERY STUFF
CELERY_BROKER_URL = "redis://localhost:6379/4"
CELERY_RESULT_BACKEND = "redis://localhost:6379/4"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Security
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_PRELOAD = True


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": ["redis://localhost:6379/4"],
        },
    }
}

ASGI_APPLICATION = "core.routing.games"

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGIN_URL = "core:login"

LOGOUT_URL = "core:logout"

LOGIN_REDIRECT_URL = "core:homepage"

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_ROOT = "/home/voron/sites/cdn/games"

STATIC_URL = "/static/"
if not DEBUG:
    # Use Google bucket for production.
    STATIC_URL = "https://storage.googleapis.com/cdn.mkeda.me/games/"

STATICFILES_DIRS = (("", os.path.join(BASE_DIR, "static")),)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

PROJECT_APPS = ["core", "games"]

JENKINS_TASKS = (
    "django_jenkins.tasks.run_pylint",
    "django_jenkins.tasks.run_pep8",
    "django_jenkins.tasks.run_pyflakes",
)


SOCIAL_AUTH_LOGIN_REDIRECT_URL = LOGIN_REDIRECT_URL
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = LOGIN_REDIRECT_URL
SOCIAL_AUTH_SANITIZE_REDIRECTS = False
SOCIAL_AUTH_FACEBOOK_KEY = get_env_var("SOCIAL_AUTH_FACEBOOK_KEY")
SOCIAL_AUTH_FACEBOOK_SECRET = get_env_var("SOCIAL_AUTH_FACEBOOK_SECRET")

EMAIL_HOST = "smtp.mailgun.org"
EMAIL_PORT = 2525
EMAIL_HOST_USER = get_env_var("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_env_var("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
MAILGUN_SERVER_NAME = "maps.mkeda.me"
EMAIL_SUBJECT_PREFIX = "[Maps]"
SERVER_EMAIL = "admin@maps.mkeda.me"

LOGGING["formatters"]["django.server"] = {
    "()": "games.utils.LogFormatter",
    "format": '["%(server_time)s", "%(levelname)s", "%(message)s"]',
}
