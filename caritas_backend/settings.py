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

SECRET_KEY = config('SECRET_KEY', default='django-insecure-(gqx4$3lehmu95g$!slo*z(uj#su^#fmzp5@m0h*w7+1=_473u')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,20.246.91.21', cast=Csv())

# ============================================================================
# CONFIGURACIÓN DE TWILIO VERIFY
# ============================================================================

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
    'corsheaders.middleware.CorsMiddleware',
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
        'OPTIONS': {},
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

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# ============================================================================
# CONFIGURACIÓN DEL MODELO DE USUARIO
# ============================================================================

AUTH_USER_MODEL = 'users.AdminUser'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# CONFIGURACIÓN DE CORS
# ============================================================================

CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://20.246.91.21:8001",
    "http://20.246.91.21",
]

CORS_ALLOW_CREDENTIALS = True

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
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.CustomTokenAuthentication',
    ],

    # Configuración específica para evitar conflictos con documentación
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Configuración específica para documentación
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ============================================================================
# CONFIGURACIÓN DE DRF SPECTACULAR (SWAGGER)
# ============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'API de Caritas Monterrey',
    'DESCRIPTION': '''
# Sistema de Gestión de Albergues - API REST

## 🔐 Autenticación

Esta API utiliza autenticación por **Token**. Para usar los endpoints protegidos:

1. **Obtener Token de Administrador**: 
   - Endpoint: `POST /api/users/auth/admin-login/`
   - Body: `{"username": "tu_usuario", "password": "tu_contraseña"}`
   - Respuesta: `{"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b", ...}`

2. **Obtener Token de Usuario Final**:
   - Endpoint: `POST /api/users/phone-verification/verify/`
   - Body: `{"phone_number": "+52811908593", "code": "123456"}`
   - Respuesta: `{"token": "abc123...", "user": {...}}`

3. **Usar Token**: 
   - Header: `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`
   - Click en el botón **"Authorize"** arriba y pega tu token

## 📋 Endpoints Públicos (No requieren autenticación)

- `POST /api/users/pre-register/` - Crear pre-registro
- `POST /api/users/pre-register/verify-phone/` - Verificar teléfono
- `POST /api/users/phone-verification/send/` - Enviar código SMS
- `POST /api/users/phone-verification/verify/` - Verificar código SMS
- `POST /api/users/auth/admin-login/` - Login de administrador

## 🔒 Endpoints Protegidos

Todos los demás endpoints requieren autenticación con token.

## 📚 Módulos Disponibles

- **Usuarios**: Pre-registros, usuarios finales, administradores
- **Albergues**: Ubicaciones, albergues, reservas de alojamiento
- **Servicios**: Servicios, horarios, reservas de servicios
- **Inventario**: Artículos, inventarios, control de stock

## 🚀 Características

- Autenticación con tokens
- Verificación SMS con Twilio
- Paginación automática (20 items por página)
- Filtros y búsqueda en todos los endpoints
- Operaciones masivas (aprobar, desactivar, etc.)
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/',
    
    # Configuración de componentes
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': True,
    'COMPONENT_SPLIT_PATCH': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    
    # Tags personalizados
    'TAGS': [
        {'name': 'Authentication', 'description': '🔐 Autenticación y login/logout'},
        {'name': 'Phone Verification', 'description': '📱 Verificación de teléfonos con SMS'},
        {'name': 'Pre-Register Users', 'description': '📝 Gestión de pre-registros de usuarios'},
        {'name': 'Custom Users', 'description': '👤 Gestión de usuarios finales del sistema'},
        {'name': 'Admin Users', 'description': '👨‍💼 Gestión de usuarios administradores'},
        {'name': 'Albergues', 'description': '🏠 Gestión de albergues, ubicaciones y reservas'},
        {'name': 'Servicios', 'description': '🍽️ Gestión de servicios y reservas'},
        {'name': 'Inventario', 'description': '📦 Gestión de inventario y artículos'},
    ],
    
    # Configuración de seguridad - Solo mostrar TokenAuth
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': ['users.authentication.CustomTokenAuthentication'],
    'SERVE_AUTHENTICATION_CLASSES': ['users.authentication.CustomTokenAuthentication'],
    
    # Configuración de Swagger UI
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
        'syntaxHighlight.theme': 'monokai',
        'defaultModelsExpandDepth': 3,
        'defaultModelExpandDepth': 3,
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'operationsSorter': 'alpha',
        'tagsSorter': 'alpha',
        # Configuración específica para mostrar solo TokenAuth
        'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
        'showRequestHeaders': True,
    },
    
    # Configuración de ReDoc
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'hideLoading': False,
        'nativeScrollbars': False,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#667eea'
                }
            },
            'typography': {
                'fontSize': '14px',
                'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            }
        }
    },
    
    # Esquemas de autenticación - Solo mostrar TokenAuth
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'TokenAuth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Token de autenticación. Formato: `Token <tu_token>` (válido para usuarios finales y administradores)'
            }
        }
    },

    'SECURITY': [{'TokenAuth': []}],  # Aplicar TokenAuth globalmente

    # Deshabilitar generación automática de esquemas de seguridad
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'DISABLE_ERRORS_AND_WARNINGS': False,
    
    # Preprocessing - Personalizar esquemas de seguridad
    'PREPROCESSING_HOOKS': [
        'drf_spectacular.hooks.preprocess_exclude_path_format',
        'caritas_backend.hooks.custom_preprocessing_hook',
    ],
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
        'caritas_backend.hooks.custom_postprocessing_hook',
    ],
    
    # Enum name overrides
    'ENUM_NAME_OVERRIDES': {},
    
    # Configuración adicional
    'CAMELIZE_NAMES': False,
    'DISABLE_ERRORS_AND_WARNINGS': False,
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

(BASE_DIR / 'logs').mkdir(exist_ok=True)

# ============================================================================
# CONFIGURACIÓN DE SEGURIDAD ADICIONAL
# ============================================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 86400
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ============================================================================
# CONFIGURACIÓN DE CACHE
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
