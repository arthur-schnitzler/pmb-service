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
    VITE_DEV = True
else:
    DEBUG = False
    VITE_DEV = False

ALLOWED_HOSTS = ["*"]
FIXTURE_DIRS = [os.path.join(BASE_DIR, "fixtures")]

APIS_LIST_VIEWS_ALLOWED = True
APIS_DETAIL_VIEWS_ALLOWED = True
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5.html"
DJANGO_TABLES2_TABLE_ATTRS = {
    "class": "table table-hover table-borderless table-relations",
}
# Application definition

INSTALLED_APPS = [
    "apis_override_select2js",
    "dal",
    "dal_select2",
    "django.contrib.humanize",
    "django_extensions",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "csvexport",
    "tinymce",
    "browsing",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "django_filters",
    "django_vite",
    "acdh_django_widgets",
    "apis_core.apis_entities",
    "apis_core.apis_metainfo",
    "apis_core.apis_relations",
    "apis_core.apis_vocabularies",
    "apis_core.apis_labels",
    "apis_core.apis_tei",
    "normdata",
    "dumper",
    "archemd",
    "network",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

CSRF_USE_SESSIONS = True


MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}

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
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
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

STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "static" / "vite",
]
# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "de"

TIME_ZONE = "Europe/Vienna"

USE_I18N = True

USE_L10N = True

USE_TZ = True
USE_THOUSAND_SEPARATOR = False


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PROJECT_NAME = "pmb"

APIS_BASE_URI = "https://pmb.acdh.oeaw.ac.at/"

REDMINE_ID = "20586"
APIS_RELATIONS_FILTER_EXCLUDE = []
CSRF_TRUSTED_ORIGINS = ["https://pmb.acdh.oeaw.ac.at"]
BIRTH_REL = [
    88,
]
DEATH_REL = [
    89,
]
PL_A_PART_OF = [
    1106,
]
PL_B_LOCATED_IN = [
    971,
]
ORG_LOCATED_IN = [
    970,
]
AUTHOR_RELS = [
    1049,
]
PL_EVENT = [
    1202,
]

OWNCLOUD_USER = os.environ.get("OWNCLOUD_USER")
OWNCLOUD_PW = os.environ.get("OWNCLOUD_PW")
PMB_LOG_FILE = os.path.join(MEDIA_ROOT, "pmb-log.csv")
PMB_TIME_PATTERN = "%Y-%m-%d::%H:%M:%S"

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

DJANGO_VITE = {
    "default": {"dev_mode": VITE_DEV, "manifest_path": "static/vite/manifest.info"}
}

DEFAULT_COLOR = "#9B5F98"
DOMAIN_MAPPING = [
    ("d-nb.info", "gnd", "#006AB3"),
    ("geonames", "geonames", "#363"),
    ("wikidata", "wikidata", "#0645ad"),
    ("wikipedia", "wikipedia", "#0645AD"),
    ("fackel.oeaw.ac.at", "fackel", "#CE0F0B"),
    ("schnitzler-tagebuch", "schnitzler-tagebuch", "#037a33"),
    ("schnitzler-bahr", "schnitzler-bahr", "#F9BD63"),
    ("schnitzler-briefe", "schnitzler-briefe", "#A63437"),
    ("schnitzler-lektueren", "schnitzler-lektueren", "#022954"),
    ("schnitzler-interviews", "schnitzler-interviews", "#3D5A80"),
    ("schnitzler-kino.", "schnitzler-kino", "#B43C9C"),
    ("//doi.org/10.1553", "oebl", "#a50021"),
    ("dx.doi.org/10.1553", "oeml", "#f0e6d2"),
    ("kraus.wienbibliothek.at", "legalkraus", "#c85545"),
    ("kraus1933", "dritte-walpurgisnacht", "#a21a17"),
    ("pmb.acdh.oeaw.ac.at", "pmb", "#9B5F98"),
    ("anno", "anno", "#b7422f"),
    ("geschichtewiki.wien", "wiengeschichtewiki", "#6F6938"),
    ("thun-korrespondenz.acdh.oeaw.ac.at", "thun-korrespondenz", "#01589C"),
    ("hanslick.acdh.oeaw.ac.at", "hanslick-online", "#222fa8"),
    ("bahr-textverzeichnis.acdh.oeaw.ac.at/pmb", "bahr-textverzeichnis", "#8E4162"),
    ("bahr-textverzeichnis.acdh.oeaw.ac.at/TSN-", "bahr-TSN", "#ce0000"),
    ("amp.acdh.oeaw.ac.at", "auden-musulin-papers", "#b59890"),
    ("schnitzler-zeitungen.", "schnitzler-zeitungen", "#8E8575"),
    ("schnitzler-mikrofilme.", "schnitzler-mikrofilme", "#6e7b8b"),
]


CSV_EXPORT_REFERENCE_DEPTH = 1
CSV_EXPORT_DELIMITER = ","
CSV_EXPORT_ESCAPECHAR = "|"
CSV_EXPORT_QUOTECHAR = '"'
CSV_EXPORT_DOUBLEQUOTE = True
CSV_EXPORT_LINETERMINATOR = r"\n"
CSV_EXPORT_QUOTING = "QUOTE_ALL"


TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 500,
    "menubar": False,
    "plugins": "advlist,autolink,lists,link,image,charmap,print,preview,anchor,"
    "searchreplace,visualblocks,code,fullscreen,insertdatetime,media,table,paste,"
    "code,help,wordcount",
    "toolbar": "undo redo | formatselect | link | code "
    "bold italic backcolor | alignleft aligncenter "
    "alignright alignjustify | bullist numlist outdent indent | "
    "removeformat | help",
}
