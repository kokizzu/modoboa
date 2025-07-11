"""
Django settings for test_project project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

from logging.handlers import SysLogHandler
import os

from modoboa.test_settings import *  # noqa


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "!8o(-dbbl3e+*bh7nx-^xysdt)1gso*%@4ze4-9_9o+i&amp;t--u_"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = "DEBUG" in os.environ

ALLOWED_HOSTS = [
    "api",
    "api-unsecured",
    "127.0.0.1",
    "localhost",
]

INTERNAL_IPS = ["127.0.0.1"]

SITE_ID = 1

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# A list of all the people who get code error notifications. When DEBUG=False
# and a view raises an exception, Django will email these people with the full
# exception information.
# See https://docs.djangoproject.com/en/dev/ref/settings/#admins
# ADMINS = [('Administrator', 'admin@example.net')]

# The email address that error messages come from, such as those sent to ADMINS
# SERVER_EMAIL = 'webmaster@example.net'
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Security settings

X_FRAME_OPTIONS = "SAMEORIGIN"
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Application definition

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "reversion",
    "oauth2_provider",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "django_rename_app",
    "django_rq",
    "django_extensions",  # Just for docker (SSL support)
)

# A dedicated place to register Modoboa applications
# Do not delete it.
# Do not change the order.
MODOBOA_APPS = (
    "modoboa",
    "modoboa.core",
    "modoboa.lib",
    "modoboa.admin",
    "modoboa.transport",
    "modoboa.relaydomains",
    "modoboa.limits",
    "modoboa.parameters",
    "modoboa.dnstools",
    "modoboa.policyd",
    "modoboa.maillog",
    "modoboa.pdfcredentials",
    "modoboa.dmarc",
    "modoboa.imap_migration",
    "modoboa.autoreply",
    "modoboa.sievefilters",
    "modoboa.rspamd",
    # Modoboa extensions here.
    "modoboa.contacts",
    "modoboa.calendars",
    "modoboa.webmail",
)

try:
    import ldap  # noqa: F401
except ImportError:
    pass
else:
    MODOBOA_APPS += ("modoboa.ldapsync",)

INSTALLED_APPS += MODOBOA_APPS

AUTH_USER_MODEL = "core.User"

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "x_forwarded_for.middleware.XForwardedForMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "modoboa.core.middleware.LocalConfigMiddleware",
    "modoboa.lib.middleware.CommonExceptionCatcher",
    "modoboa.lib.middleware.RequestCatcherMiddleware",
)

AUTHENTICATION_BACKENDS = (
    # 'modoboa.lib.authbackends.LDAPBackend',
    # 'modoboa.lib.authbackends.SMTPBackend',
    "django.contrib.auth.backends.ModelBackend",
    "modoboa.imap_migration.auth_backends.IMAPBackend",
)

# SMTP authentication
# AUTH_SMTP_SERVER_ADDRESS = 'localhost'
# AUTH_SMTP_SERVER_PORT = 25
# AUTH_SMTP_SECURED_MODE = None  # 'ssl' or 'starttls' are accepted


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    },
]

ROOT_URLCONF = "test_project.urls"

WSGI_APPLICATION = "test_project.wsgi.application"

CORS_ORIGIN_ALLOW_ALL = True

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/sitestatic/"
STATIC_ROOT = os.path.join(BASE_DIR, "sitestatic")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# oAuth2 settings

OIDC_RSA_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQCbCYh5h2NmQuBqVO6G+/CO+cHm9VBzsb0MeA6bbQfDnbhstVOT
j0hcnZJzDjYc6ajBZZf6gxVP9xrdm9Uh599VI3X5PFXLbMHrmzTAMzCGIyg+/fnP
0gocYxmCX2+XKyj/Zvt1pUX8VAN2AhrJSfxNDKUHERTVEV9bRBJg4F0C3wIDAQAB
AoGAP+i4nNw+Ec/8oWh8YSFm4xE6qKG0NdTtSMAOyWwy+KTB+vHuT1QPsLn1vj77
+IQrX/moogg6F1oV9YdA3vat3U7rwt1sBGsRrLhA+Spp9WEQtglguNo4+QfVo2ju
YBa2rG+h75qjiA3xnU//F3rvwnAsOWv0NUVdVeguyR+u6okCQQDBUmgWeH2WHmUn
2nLNCz+9wj28rqhfOr9Ptem2gqk+ywJmuIr4Y5S1OdavOr2UZxOcEwncJ/MLVYQq
MH+x4V5HAkEAzU2GMR5OdVLcxfVTjzuIC76paoHVWnLibd1cdANpPmE6SM+pf5el
fVSwuH9Fmlizu8GiPCxbJUoXB/J1tGEKqQJBALhClEU+qOzpoZ6/voYi/6kdN3zc
uEy0EN6n09AKb8gS9QH1STgAqh+ltjMkeMe3C2DKYK5/QU9/Pc58lWl1FkcCQG67
ZamQgxjcvJ85FvymS1aqW45KwNysIlzHjFo2jMlMf7dN6kobbPMQftDENLJvLWIT
qoFyGycdsxZiPAIyZSECQQCZFn3Dl6hnJxWZH8Fsa9hj79kZ/WVkIXGmtdgt0fNr
dTnvCVtA59ne4LEVie/PMH/odQWY0SxVm/76uBZv/1vY
-----END RSA PRIVATE KEY-----"""  # DEV ONLY

OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    "OIDC_RP_INITIATED_LOGOUT_ENABLED": True,
    "OIDC_RP_INITIATED_LOGOUT_ALWAYS_PROMPT": False,
    "OIDC_RSA_PRIVATE_KEY": OIDC_RSA_PRIVATE_KEY,  # PROD : os.environ.get("OIDC_RSA_PRIVATE_KEY"),
    "SCOPES": {
        "openid": "OpenID Connect scope",
        "read": "Read scope",
        "write": "Write scope",
        "introspection": "Introspect token scope",
    },
    "DEFAULT_SCOPES": ["openid", "read", "write"],
}

# Rest framework settings

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "user": "400/minute",
        "ddos": "50/second",
        "ddos_lesser": "200/minute",
        "login": "10/minute",
        "password_recovery_request": "12/hour",
        "password_recovery_totp_check": "25/hour",
        "password_recovery_apply": "25/hour",
    },
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
}

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "TITLE": "Modoboa API",
    "VERSION": None,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
}

# Modoboa settings
# MODOBOA_CUSTOM_LOGO = os.path.join(MEDIA_URL, "custom_logo.png")

# DOVECOT_LOOKUP_PATH = ('/path/to/dovecot', )
DOVECOT_USER = "root"

MODOBOA_API_URL = "https://api.modoboa.org/1/"

PID_FILE_STORAGE_PATH = "/tmp"

# REDIS

REDIS_SENTINEL = bool(os.environ.get("REDIS_SENTINEL", False))
REDIS_SENTINELS = [
    (
        os.environ.get("REDIS_SENTINEL_HOST", "127.0.0.1"),
        os.environ.get("REDIS_SENTINEL_PORT", 26379),
    )
]
REDIS_MASTER = os.environ.get("REDIS_MASTER", "mymaster")

REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_QUOTA_DB = 0
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_QUOTA_DB}"

# RQ

RQ_QUEUES = {
    "dkim": {
        "URL": REDIS_URL,
    },
    "modoboa": {
        "URL": REDIS_URL,
    },
}

# CACHE

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}",
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
    {
        "NAME": "modoboa.core.password_validation.ComplexityValidator",
        "OPTIONS": {"upper": 1, "lower": 1, "digits": 1, "specials": 0},
    },
]

# Logging configuration

LOGGING = {
    "version": 1,
    "formatters": {
        "syslog": {"format": "%(name)s: %(levelname)s %(message)s"},
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        },
    },
    "handlers": {
        "mail-admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
        "syslog-auth": {
            "class": "logging.handlers.SysLogHandler",
            "facility": SysLogHandler.LOG_AUTH,
            "formatter": "syslog",
        },
        "modoboa": {
            "class": "modoboa.core.loggers.SQLHandler",
        },
        "console": {"class": "logging.StreamHandler"},
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
    },
    "loggers": {
        "django": {"handlers": ["mail-admins"], "level": "ERROR", "propagate": False},
        "modoboa.auth": {
            "handlers": ["syslog-auth", "modoboa"],
            "level": "INFO",
            "propagate": False,
        },
        "modoboa.admin": {"handlers": ["modoboa"], "level": "INFO", "propagate": False},
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        # 'django_auth_ldap': {
        #     'level': 'DEBUG',
        #     'handlers': ['console']
        # },
    },
}

SILENCED_SYSTEM_CHECKS = [
    "security.W019",  # modoboa uses iframes to display e-mails
]

DISABLE_DASHBOARD_EXTERNAL_QUERIES = False

# Load settings from extensions

LDAP_SERVER_PORT = os.environ.get("LDAP_SERVER_PORT", 3389)

WEBMAIL_DEV_MODE = os.environ.get("WEBMAIL_DEV_MODE", "off") == "on"
WEBMAIL_DEV_USERNAME = os.environ.get("WEBMAIL_DEV_USERNAME", "")
WEBMAIL_DEV_PASSWORD = os.environ.get("WEBMAIL_DEV_PASSWORD", "")
