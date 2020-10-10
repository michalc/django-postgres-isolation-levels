from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'not-a-secret'
DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = ['app']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
