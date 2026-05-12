import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Auto-add Railway domain if present
RAILWAY_HOST = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
if RAILWAY_HOST and RAILWAY_HOST not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RAILWAY_HOST)

# Allow all hosts in production if explicitly set
if os.getenv('ALLOW_ALL_HOSTS', 'False') == 'True':
    ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'rest_framework',
    'task_a',
    'task_b',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
MODEL_NAME = os.getenv('MODEL_NAME', 'meta-llama/Llama-4-Scout-17B-16E-Instruct')
DATA_DIR = BASE_DIR / 'data'
SAMPLE_DATA_PATH = DATA_DIR / 'sample' / 'reviews_sample.csv'
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

# Railway healthcheck host
ALLOWED_HOSTS += ['healthcheck.railway.app', '.railway.app', '.up.railway.app']
