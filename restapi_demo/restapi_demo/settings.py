import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k66@8h#l-*a7$hozy0d3)z3+g0rnmq1bo3@r81$0!g%826-uz0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

load_dotenv()                           # load .env file

env_path = Path('.') / '.env'           # path of given .env
load_dotenv(dotenv_path=env_path)

# Email verification

EMAIL_USE_TLS = True  # Email Tool
EMAIL_HOST = os.getenv("EMAIL_HOST")  # gmail use SMTP protocol
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")  # from email id
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")  # password
EMAIL_PORT = 587  # email port default

# Social login

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.RemoteUserBackend',
    'social_core.backends.github.GithubOAuth2',
)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'apidemo',
    'rest_framework.authentication',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'storages',
    'social_django',
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# django.core.mail.backends.smtp.EmailBackend
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

REST_FRAMEWORK = {
  'DEFAULT_AUTHENTICATION_CLASSES': (
    'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
  ),
}

ROOT_URLCONF = 'restapi_demo.urls'

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

                'social_django.context_processors.backends',  # Social login
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'restapi_demo.wsgi.application'

# Postgresql Database configuration

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv("DATABASE_NAME"),
        'USER': os.getenv("DATABASE_USER"),
        'PASSWORD': os.getenv("DATABASE_PASSWORD"),
        'HOST': 'localhost',
        'PORT': '',
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_LOCATION"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },

    }
}

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
LOGOUT_REDIRECT_URL = 'log_me/'
CACHE_TTL = 60 * 15                 # redis cache timeout in minutes

SOCIAL_AUTH_GITHUB_KEY = os.getenv("GIT_CLI_ID")            # github login key
SOCIAL_AUTH_GITHUB_SECRET = os.getenv("GIT_SECRET_CLI")

LOGIN_URL = 'RestLogin'
LOGOUT_URL = ''
LOGIN_REDIRECT_URL = 'RestLogin'

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")      # rabitMQ broker
