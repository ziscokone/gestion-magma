"""
Django settings for MAGMA (gestion de salle de sport) — structure de base, usage local.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as message_constants

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError("La variable d'environnement SECRET_KEY est obligatoire.")
SECRET_KEY = _secret_key

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

_allowed_hosts = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Sécurité
    'axes',

    # Local apps
    'core',
    'apps.etablissement',
    'apps.comptes',
    'apps.clients',
    'apps.abonnements',
    'apps.stock',
    'apps.budget',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.etablissement.context_processors.etablissement_context',
                'core.context_processors.active_module',
                'core.context_processors.modules_actifs',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Base de données — SQLite en local uniquement (pas de config prod à ce stade)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'comptes.Utilisateur'


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]


LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True


# Django utilise le niveau "error" pour messages.error(), mais Bootstrap 5
# attend la classe "danger" (pas de classe alert-error) pour l'affichage rouge.
MESSAGE_TAGS = {
    message_constants.ERROR: 'danger',
}


STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Connexion / déconnexion
LOGIN_URL = 'comptes:login'
LOGIN_REDIRECT_URL = 'hub'
LOGOUT_REDIRECT_URL = 'comptes:login'

# ─── Django Axes (protection brute force) — pile sécurité allégée pour démarrer ──
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ADMIN = True
AXES_VERBOSE = False
