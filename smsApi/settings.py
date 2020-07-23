import django_heroku
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

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
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

#SECRET_KEY = os.environ.get('SECRET_KEY', "sdjsdshhskdj")
DEBUG = True

ALLOWED_HOSTS = ['*']  ##allows all hosts

#Devops suggested we include this for deployment
SECRET_KEY= 'lmrffsgfhrilklg-za7#57vi!zr)ps8)2anyona25###dl)s-#s=7=vn_'
# TWILIO_ACCOUNT_SID = 'AC24dc3ff423be936f3efd0503045fd4e8'
# TWILIO_AUTH_TOKEN = '70846d53642b6fc91abb485b88a0fa96'
# TWILIO_NUMBER = '+13026637959'
# TELESIGN_API = 'mp6UoFnveiSDjHSQmNdNxLrpNca844of69XAWOHYu+xRZsadpUm5XsQ50utSNAzOl/tj3lOxQMIwlmaHXL2cxQ=='
# TELESIGN_CUST = '163CFEDD-EB4D-4DEE-949C-9F44F6292FA5'
# #MessageBird
# MB_ACCESS_KEY = 'T9KCkelsJGqAwRU6Htdy2LI7m'
# #Gatewayapi.com
# GA_KEY='OCALazyE4I9G26K7fXiMcdyn'
# GA_SECRET='F-ltreMai8m-M2QMtWsVoTNF&4RU4XmAUjC^4l*d'
# #D7
# D7_TOKEN= 'dmF5aTIxODA6VjRjNUZmRm4='
# D7_USERNAME= 'vayi2180'
# D7_PASSWORD= 'V4c5FfFn'

#add twillio sid , authentication token and your twilio number
# TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID") # obtained from twilio.com/console 
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN") # also obtained from twilio.com/console 
# TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")  # use the number you received when signing up or buy a new number 


# add infobip login credentials
#INFOBIP_USERNAME = os.getenv("INFOBIP_USERNAME")
#INFOBIP_PASSWORD = os.getenv("INFOBIP_PASSWORD")
#INFOBIP_APIKEY = os.getenv("INFOBIP_APIKEY")

# add Telesign credentials
# TELESIGN_API = os.getenv("TELESIGN_API")
# TELESIGN_CUST = os.getenv("TELESIGN_CUST")

# Application definition
#celery config
CELERY_BROKER_URL = 'amqp://rabbitmq'
# CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_BACKEND = 'db+sqlite:///db.sqlite3'
CELERY_RESULT_EXTENDED = True

# Q_CLUSTER = {
#     'name': 'DjangORM',
#     'workers': 4,
#     'timeout': 90,
#     'retry': 120,
#     'queue_limit': 50,
#     'bulk': 10,
#     'orm': 'default'
# }


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    # 'rest_framework_swagger',
    'smsApp.apps.SmsappConfig',
    'django_twilio',
    'sms_api_interface',
    'broadcast',
    'drf_yasg',
    'coreapi',
    'django_celery_results',
    'django_celery_beat',
    'phonenumber_field',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # whitenoise middleware
]

ROOT_URLCONF = 'smsApi.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'smsApi.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': (
        'rest_framework.schemas.coreapi.AutoSchema'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DATETIME_FORMAT': "%Y-%m-%dT%H:%M:%S.%fZ",
}

# AUTH_USER_MODEL = "smsApp.User"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

MEDIA_ROOT = os.path.join(BASE_DIR,'media')
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
PROJECT_ROOT = os.path.join(os.path.abspath(__file__))

# STATIC_ROOT  =   os.path.join(PROJECT_ROOT, 'static')
# FORCE_SCRIPT_NAME = '/smsApp'
# STATIC_URL = FORCE_SCRIPT_NAME + '/static/'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Extra lookup directories for collectstatic to find static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

#  Add configuration for static files storage using whitenoise
# STATICFILES_STORAGE = 'whitenoise.django.CompressedManifestStaticFilesStorage'
logger.error("In settings.py, works fine")
# Activate Django-Heroku.
django_heroku.settings(locals())
