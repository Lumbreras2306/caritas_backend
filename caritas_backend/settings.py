"""
Django settings for caritas_backend project.
"""

from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# ============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-(gqx4$3lehmu95g$!slo*z(uj#su^#fmzp5@m0h*w7+1=_473u')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,20.246.91.21', cast=Csv())

# ============================================================================
# CONFIGURACIÓN DE TWILIO VERIFY
# ============================================================================

# Twilio Configuration - Usando variables oficiales
# Variables de entorno requeridas:
# TWILIO_ACCOUNT_SID=SID (Tu Account SID de Twilio)
# TWILIO_AUTH_TOKEN=TOKEN (Tu Auth Token de Twilio)
# TWILIO_VERIFY_SERVICE_SID=SERVICE_SID (Tu Verify Service SID)

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_VERIFY_SERVICE_SID = config('TWILIO_VERIFY_SERVICE_SID', default='')

# ============================================================================
# DEFINICIÓN DE APLICACIONES
# ============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
]

LOCAL_APPS = [
    'users',
    'albergues',
    'inventory',
    'services',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================================================
# CONFIGURACIÓN DE MIDDLEWARE
# ============================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Debe estar al principio
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'caritas_backend.urls'

# ============================================================================
# CONFIGURACIÓN DE PLANTILLAS
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'caritas_backend.wsgi.application'

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='caritas_db'),
        'USER': config('DB_USER', default='caritas_user'),
        'PASSWORD': config('DB_PASSWORD', default='password123'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
        'OPTIONS': {
        },
    }
}

# ============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================================
# CONFIGURACIÓN DE INTERNACIONALIZACIÓN
# ============================================================================

LANGUAGE_CODE = config('LANGUAGE_CODE', default='es-mx')
TIME_ZONE = config('TIME_ZONE', default='America/Mexico_City')
USE_I18N = True
USE_TZ = True

# ============================================================================
# CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================================================

STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = config('STATIC_ROOT', default=BASE_DIR / 'staticfiles')

MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')

# Directorios adicionales para archivos estáticos
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# ============================================================================
# CONFIGURACIÓN DEL MODELO DE USUARIO
# ============================================================================

# Modelo de usuario personalizado para administradores
AUTH_USER_MODEL = 'users.AdminUser'

# Campo de auto incremento por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# CONFIGURACIÓN DE CORS
# ============================================================================

# Configuración CORS para desarrollo
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Solo en desarrollo

# URLs permitidas en producción
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # React dev server alternativo
    "http://127.0.0.1:3000",
    "http://localhost:8001",  # Backend en puerto 8001
    "http://127.0.0.1:8001",
    "http://20.246.91.21:8001",  # IP externa en puerto 8001
    "http://20.246.91.21",  # IP externa sin puerto
]

# Permitir credenciales
CORS_ALLOW_CREDENTIALS = True

# Headers permitidos
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ============================================================================
# CONFIGURACIÓN DE DJANGO REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    # Configuración de autenticación
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.CustomTokenAuthentication',  # Autenticación personalizada para ambos tipos de usuarios
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # Configuración de permisos
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Configuración de filtros
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Configuración de paginación
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    
    # Configuración de renderizado
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    
    # Configuración de parsers
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    
    # Manejo de excepciones
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    
    # Configuración de esquema
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ============================================================================
# CONFIGURACIÓN DE DRF SPECTACULAR (SWAGGER AUTOMÁTICO)
# ============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'API de Caritas Monterrey',
    'DESCRIPTION': '''
    Sistema de Gestión de Albergues - API REST completa
    
    ## 🔐 Autenticación
    
    Esta API utiliza autenticación por **Token de Administrador**. Para usar los endpoints protegidos:
    
    1. **Obtener Token**: Usa el endpoint `/api/users/auth/admin-login/` con tus credenciales de administrador
    2. **Usar Token**: Incluye el token en el header `Authorization: Token <tu_token>`
    3. **Ejemplo**: `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`
    
    ## 📋 Endpoints Públicos (No requieren autenticación)
    - `POST /api/users/pre-register/` - Crear pre-registro
    - `POST /api/users/pre-register/verify-phone/` - Verificar teléfono
    - `POST /api/users/phone-verification/send/` - Enviar código SMS
    - `POST /api/users/phone-verification/verify/` - Verificar código SMS
    
    ## 🔒 Endpoints Protegidos (Requieren token de administrador)
    - Todos los demás endpoints requieren autenticación
    - Usa el botón "Authorize" en la esquina superior derecha para configurar tu token
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': True,
    'COMPONENT_SPLIT_PATCH': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'OPERATION_ID_GENERATOR': 'drf_spectacular.utils.camelize_operation_id',
    'TAGS': [
        {'name': 'Pre-Register Users', 'description': 'Gestión de pre-registros de usuarios'},
        {'name': 'Custom Users', 'description': 'Gestión de usuarios finales del sistema'},
        {'name': 'Admin Users', 'description': 'Gestión de usuarios administradores'},
        {'name': 'Phone Verification', 'description': 'Verificación de números de teléfono'},
        {'name': 'Authentication', 'description': 'Autenticación y login/logout'},
        {'name': 'Albergues', 'description': 'Gestión de albergues, ubicaciones y reservas'},
        {'name': 'Servicios', 'description': 'Gestión de servicios y reservas de servicios'},
        {'name': 'Inventario', 'description': 'Gestión de inventario y artículos'},
    ],
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': None,
    'ENUM_NAME_OVERRIDES': {
        'StatusF02Enum': 'StatusEnum',
        'StatusDb8Enum': 'StatusEnum',
    },
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
        'requestInterceptor': '''
        function(request) {
            // Agregar token automáticamente si está disponible
            const token = localStorage.getItem('swagger-ui-token');
            if (token) {
                request.headers['Authorization'] = 'Token ' + token;
            }
            return request;
        }
        ''',
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'hideLoading': False,
        'nativeScrollbars': False,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#32329f'
                }
            }
        }
    },
    # Configuración de esquemas de seguridad
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Token de autenticación de administrador. Formato: Token <tu_token>'
        }
    },
    'SECURITY': [
        {
            'Token': []
        }
    ],
    # Configuración para mostrar esquemas de seguridad en operaciones
    'AUTHENTICATION_WHITELIST': [
        'users.authentication.CustomTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'PARSER_WHITELIST': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Crear directorio de logs si no existe
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD ADICIONAL
# ============================================================================

# Configuración de seguridad para producción
if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookies seguras
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Headers de seguridad
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 86400
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ============================================================================
# CONFIGURACIÓN DE CACHE (OPCIONAL)
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'caritas',
        'TIMEOUT': 300,
    } if config('USE_REDIS', default=False, cast=bool) else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'caritas-cache',
    }
}

