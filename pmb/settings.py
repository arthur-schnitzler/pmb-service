import os
import pmb.tasks  # noqa: F401

from pathlib import Path
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-vz%#&+qlze@#cfc8aakgx2vy@k^cl)$$y%te#&q%u*_vd&rwlt'

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ.get('DEBUG'):
    DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apis_core.apis_entities',
    'apis_core.apis_metainfo',
    'apis_core.apis_relations',
    'apis_core.apis_vocabularies',
    'apis_core.apis_labels',
    'apis_core.apis_tei',
    'guardian',
    'dumper',
]

if os.environ.get('DEV'):
    print('HALLLLLLOOOOO')
    INSTALLED_APPS = INSTALLED_APPS + ['django_extensions', ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pmb.urls'

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

WSGI_APPLICATION = 'pmb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('APIS_DB_NAME', 'pmb'),
        'USER': os.environ.get('APIS_DB_USER', 'pmb'),
        'PASSWORD': os.environ.get('APIS_DB_PASSWORD'),
        'HOST': os.environ.get('APIS_DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('APIS_DB_PORT', '3306'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')
STATIC_URL = 'static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_URL = 'media/'

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Vienna'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

PROJECT_NAME = "pmb"

APIS_BASE_URI = "https://pmb.acdh.oeaw.ac.at/"

REDMINE_ID = "13424"
APIS_RELATIONS_FILTER_EXCLUDE = []
CSRF_TRUSTED_ORIGINS = ['pmb.acdh.oeaw.ac.at']
BIRTH_REL = [88, ]
DEATH_REL = [89, ]
PL_A_PART_OF = [1106, 1136]
PL_B_LOCATED_IN = [971, ]
ORG_LOCATED_IN = [1141, 970, 1160]
AUTHOR_RELS = [1049, ]

CELERY_BROKER_URL = os.environ.get('amqp://')

CELERY_BEAT_SCHEDULE = {
    "mint_wikidata_ids": {
        "task": "pmb.tasks.mint_wikidata_ids",
        "schedule": crontab(hour=23, minute=45),
    },
    "fix_the_domains": {
        "task": "pmb.tasks.fix_the_domains",
        "schedule": crontab(hour=5, minute=30),
    },
    "dump_to_tei": {
        "task": "pmb.tasks.dump_to_tei",
        "schedule": crontab(hour=2, minute=2),
    },
}

OWNCLOUD_USER = os.environ.get('OWNCLOUD_USER')
OWNCLOUD_PW = os.environ.get('OWNCLOUD_PW')
PMB_LOG_FILE = os.path.join(MEDIA_ROOT, "pmb-log.csv")
PMB_TIME_PATTERN = "%Y-%m-%d::%H:%M:%S"
