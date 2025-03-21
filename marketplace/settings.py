import os
from pathlib import Path
import dj_database_url  # Для работы с DATABASE_URL от render.com
from decouple import config


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Для продакшена рекомендуется сгенерировать новый секретный ключ
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-0w+_*%hwspl5i9b)%9!i-3$dq5(e7i%e9*lh=v!u$4brh!5ok9')

# SECURITY WARNING: don't run with debug turned on in production!
# Для продакшена на render.com устанавливаем DEBUG = False
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# Настройка ALLOWED_HOSTS для render.com
# В продакшене замените '*' на ваш домен, например, ['startup-platform.onrender.com']
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',  # Для улучшения форм в шаблонах
    'accounts',       # Ваше приложение
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Для статических файлов
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'marketplace.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Если у вас есть общие шаблоны вне приложений, добавьте их сюда
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

WSGI_APPLICATION = 'marketplace.wsgi.application'

# Database
# Используем DATABASE_URL от render.com для подключения к PostgreSQL
DATABASES = {
    'default': dj_database_url.config(
        default='postgres://admin:aYNUwQ0YGogGyWIXoUwcNk6sQ5TMZBRd@dpg-cv2qcu0fnakc738e720g-a.frankfurt-postgres.render.com/marketplace_d1gj',
        conn_max_age=600
    )
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Кодировка по умолчанию
DEFAULT_CHARSET = 'utf-8'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
# Статические файлы
STATIC_URL = '/static/'  # URL для доступа к статическим файлам
STATICFILES_DIRS = [BASE_DIR / "static"]  # Папка, где лежат исходные CSS, JS, изображения
STATIC_ROOT = BASE_DIR / "staticfiles"    # Папка для собранных статических файлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Медиафайлы
MEDIA_URL = '/media/'  # URL для доступа к медиафайлам
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Кастомная модель пользователя
AUTH_USER_MODEL = 'accounts.Users'

# Логирование для отладки
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# settings.py

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')

AWS_STORAGE_BUCKET_NAME = '1-st-test-bucket-for-startup-platform-3gb-1'  # Замени на имя твоего бакета
AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net'
AWS_S3_REGION_NAME = 'ru-central1'  # Можно указать любую зону, например 'us-east-1'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_ADDRESSING_STYLE = 'path'  # Для совместимости с Yandex

# Если файлы должны быть публично доступны (например, для отображения изображений)
AWS_DEFAULT_ACL = 'public-read'





# Настройки для HTTPS на render.com
# Render автоматически использует HTTPS, но Django должен это учитывать
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Отключаем принудительный редирект на HTTPS (render.com сам это делает)
SESSION_COOKIE_SECURE = True  # Куки только через HTTPS
CSRF_COOKIE_SECURE = True     # CSRF-токены только через HTTPS

# Дополнительные настройки безопасности для продакшена
SECURE_HSTS_SECONDS = 31536000  # Включаем HSTS на год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'