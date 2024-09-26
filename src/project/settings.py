from json import JSONEncoder
from uuid import UUID
import os

from sentry_sdk.integrations.django import DjangoIntegration
import sentry_sdk


default_json_encoder = JSONEncoder.default


def custom_json_encoder(self, obj):
    """
        Sobrecarga JSONEncoder para soporte serializar UUID.
        Ref. https://arthurpemberton.com/2015/04/fixing-uuid-is-not-json-serializable
    """
    if isinstance(obj, UUID):
        return str(obj)

    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    return default_json_encoder(self, obj)


JSONEncoder.default = custom_json_encoder


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '4opycm9%z=zpo==49q(1ilh&(@9vxxn30(9z6yb&elsemj@@dm'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'dal',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    # LOCAL APPS
    'apps.ubigeo',
    'apps.arcsubs',
    'apps.signwall',
    # EXTERNAL APPS
    'django_json_widget',
    'drf_yasg',
    'import_export',
    'rangefilter',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'middleware_prod_viernes',
        'USER': 'postgres',
        'PASSWORD': '123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Lima'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

MEDIA_URL = '/media/'

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_ROOT = os.path.join(BASE_DIR, 'static_files')

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'), )


####################
# PROJECT SETTINGS #
####################


##################
# LOCAL SETTINGS #
##################

# Allow any settings to be defined in local.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from .local_settings import *
except ImportError:
    pass


##################
# DEBUG SETTINGS #
##################

# SENTRY
sentry_sdk.init(
    dsn=SENTRY_DNS,
    integrations=[DjangoIntegration(), ],
    environment=ENVIRONMENT,
    debug=ENVIRONMENT != 'production',
)


INTERNAL_IPS = ('127.0.0.1', )
if DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        INSTALLED_APPS += ('debug_toolbar', )
        MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

    try:
        import django_extensions
    except ImportError:
        pass
    else:
        INSTALLED_APPS += ('django_extensions', )
