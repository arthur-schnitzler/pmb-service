import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-vz%#&+qlze@#cfc8aakgx2vy@k^cl)$$y%te#&q%u*_vd&rwlt"

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ.get("DEBUG"):
    DEBUG = True

ALLOWED_HOSTS = ["*"]

APIS_LIST_VIEWS_ALLOWED = True
APIS_DETAIL_VIEWS_ALLOWED = True


# Application definition

INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "browsing",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "django_filters",
    "apis_core.apis_entities",
    "apis_core.apis_metainfo",
    "apis_core.apis_relations",
    "apis_core.apis_vocabularies",
    "apis_core.apis_labels",
    "apis_core.apis_tei",
    "dumper",
    "archemd",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

if os.environ.get("DEV"):
    INSTALLED_APPS = INSTALLED_APPS + [
        "django_extensions",
    ]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pmb.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "pmb.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "pmb"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTEGRES_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles/")
STATIC_URL = "static/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
MEDIA_URL = "media/"

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Vienna"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PROJECT_NAME = "pmb"

APIS_BASE_URI = "https://pmb.acdh.oeaw.ac.at/"

REDMINE_ID = "13424"
APIS_RELATIONS_FILTER_EXCLUDE = []
CSRF_TRUSTED_ORIGINS = ["https://pmb.acdh.oeaw.ac.at"]
BIRTH_REL = [
    88,
]
DEATH_REL = [
    89,
]
PL_A_PART_OF = [1106, 1136]
PL_B_LOCATED_IN = [
    971,
]
ORG_LOCATED_IN = [1141, 970, 1160]
AUTHOR_RELS = [
    1049,
]

OWNCLOUD_USER = os.environ.get("OWNCLOUD_USER")
OWNCLOUD_PW = os.environ.get("OWNCLOUD_PW")
PMB_LOG_FILE = os.path.join(MEDIA_ROOT, "pmb-log.csv")
PMB_TIME_PATTERN = "%Y-%m-%d::%H:%M:%S"
PMB_DETAIL_VIEW_PATTERN = (
    "https://pmb.acdh.oeaw.ac.at/apis/entities/entity/{}/{}/detail"
)
APIS_ENTITIES = {
    "Place": {
        "merge": True,
        "search": ["name"],
        "form_order": ["name", "kind", "lat", "lng", "status", "collection"],
        "table_fields": ["name"],
        "additional_cols": ["id", "lat", "lng", "part_of"],
        "list_filters": [
            {"name": {"method": "name_label_filter"}},
            {"collection": {"label": "Collection"}},
            {"kind": {"label": "Kind of Place"}},
            "related_entity_name",
            "related_relationtype_name",
            "lat",
            "lng",
        ],
    },
    "Person": {
        "merge": True,
        "search": ["name", "first_name"],
        "form_order": [
            "first_name",
            "name",
            "start_date_written",
            "end_date_written",
            "profession",
            "status",
            "collection",
        ],
        "table_fields": [
            "name",
            "first_name",
            "start_date_written",
            "end_date_written",
        ],
        "additional_cols": ["id", "profession", "gender"],
        "list_filters": [
            "name",
            {"gender": {"label": "Gender"}},
            {"start_date": {"label": "Date of Birth"}},
            {"end_date": {"label": "Date of Death"}},
            {"profession": {"label": "Profession"}},
            {"title": {"label": "Title"}},
            {"collection": {"label": "Collection"}},
            "related_entity_name",
            "related_relationtype_name",
        ],
    },
    "Institution": {
        "merge": True,
        "search": ["name"],
        "form_order": [
            "name",
            "start_date_written",
            "end_date_written",
            "kind",
            "status",
            "collection",
        ],
        "additional_cols": [
            "id",
            "kind",
        ],
        "list_filters": [
            {"name": {"label": "Name or label of institution"}},
            {"kind": {"label": "Kind of Institution"}},
            {"start_date": {"label": "Date of foundation"}},
            {"end_date": {"label": "Date of termination"}},
            {"collection": {"label": "Collection"}},
            "related_entity_name",
            "related_relationtype_name",
        ],
    },
    "Work": {
        "merge": True,
        "search": ["name"],
        "additional_cols": [
            "id",
            "kind",
        ],
        "list_filters": [
            {"name": {"label": "Name of work"}},
            {"kind": {"label": "Kind of Work"}},
            {"start_date": {"label": "Date of creation"}},
            {"collection": {"label": "Collection"}},
            "related_entity_name",
            "related_relationtype_name",
        ],
    },
    "Event": {
        "merge": True,
        "search": ["name"],
        "additional_cols": [
            "id",
        ],
        "list_filters": [
            {"name": {"label": "Name of event"}},
            {"kind": {"label": "Kind of Event"}},
            {"start_date": {"label": "Date of beginning"}},
            {"end_date": {"label": "Date of end"}},
            {"collection": {"label": "Collection"}},
            "related_entity_name",
            "related_relationtype_name",
        ],
    },
}
