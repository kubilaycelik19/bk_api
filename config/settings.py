import dj_database_url
import os
from dotenv import load_dotenv
load_dotenv() # .env dosyasındaki ortam değişkenlerini yükle
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# config/settings.py
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    '127.0.0.1',  # Yerel (local) testimiz için
    'localhost',
    'bk-api-evsk.onrender.com',
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'users.apps.UsersConfig',
    'appointments.apps.AppointmentsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'config.middleware.DebugMiddleware',  # Debug middleware'i en başa ekle
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


DATABASES = {
    'default': dj_database_url.config(

        default=f'sqlite:///{os.path.join(BASE_DIR, "db.sqlite3")}',
        
        # Veritabanı bağlantı ömrü
        conn_max_age=600
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser' # Standart User modeli yerine CustomUser modelini kullanmak için eklenen satır

# Django REST Framework ve Simple JWT ayarları. DRF(Django Rest Framework) artık JWT ile kimlik doğrulama yapacak şekilde yapılandırıldı. Yani Token ile çalışacak.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Custom exception handler - Tutarlı hata yönetimi için
    #'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
}

# Güvendiğimiz Frontend adreslerinin listesi
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500", # Live Server adresimiz
    "http://localhost:5500",  # Live Server'ın diğer adı

    # React Vite geliştirme sunucusu adresleri
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://bk-frontend-react-78c4.vercel.app",
]

# Preview alan adları için esnek izin (opsiyonel)
# CORS_ALLOWED_ORIGIN_REGEXES = [r'^https://.*\\.vercel\\.app$']

# CSRF güvenilir originler (form/cookie senaryoları için)
CSRF_TRUSTED_ORIGINS = [
    "https://bk-frontend-react-78c4.vercel.app",
]

# Kural 1: Hangi metodlara (GET, POST, OPTIONS) izin verileceği
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS', # Uçuş öncesi (Preflight) isteği için bu ZORUNLU
    'PATCH',
    'POST',
    'PUT',
]

# Kural 2: Hangi özel başlıklara (header) izin verileceği
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization', # Bu, bizim 'Bearer ${accessToken}' için KRİTİK
    'content-type',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Canlıda Admin Paneli CSS/JS dosyaları için ayarlar
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Proxy arkasında doğru scheme/host için
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# DRF Pagination (ileride eklenecek). Şimdilik kapalı, frontend dizi bekliyor.

# Email Configuration
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))

# SSL/TLS Configuration
# Render'da port 465 (SSL) çalışabilir, port 587 (TLS) bloklanmış olabilir
# Port 465 kullanıyorsanız: EMAIL_USE_SSL=True, EMAIL_USE_TLS=False
# Port 587 kullanıyorsanız: EMAIL_USE_TLS=True, EMAIL_USE_SSL=False
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True' if not EMAIL_USE_SSL else False

# Gmail adresin (.env dosyasından çekiliyor)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')

# Gmail uygulama şifresi (16 haneli) - .env dosyasından çekiliyor
# DİKKAT: Normal Gmail şifrenizi değil, Google Hesabınızdan alacağınız "Uygulama Şifresi"ni kullanın
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Email timeout (Render'da network sorunları için)
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))  # 10 saniye

# Giden maillerde görünecek adres
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER if EMAIL_HOST_USER else None
SERVER_EMAIL = EMAIL_HOST_USER if EMAIL_HOST_USER else None

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'appointments': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Tüm logları görmek için DEBUG
            'propagate': False,
        },
        'appointments.signals': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'appointments.email_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
