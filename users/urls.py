# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PreRegisterUserViewSet,
    CustomUserViewSet,
    AdminUserViewSet,
    PhoneVerificationViewSet,
    AdminUserLoginView,
    AdminUserLogoutView,
    CustomObtainAuthToken,
)

# ============================================================================
# CONFIGURACIÓN DE ROUTERS
# ============================================================================

# Router principal para ViewSets
router = DefaultRouter()

# Registrar ViewSets en el router
router.register(r'pre-register', PreRegisterUserViewSet, basename='preregisteruser')
router.register(r'customers', CustomUserViewSet, basename='customuser')
router.register(r'admins', AdminUserViewSet, basename='adminuser')
router.register(r'phone-verification', PhoneVerificationViewSet, basename='phoneverification')

# ============================================================================
# PATRONES DE URL
# ============================================================================

urlpatterns = [
    # URLs generadas automáticamente por el router
    path('', include(router.urls)),
    
    # ========================================================================
    # ENDPOINTS DE AUTENTICACIÓN
    # ========================================================================
    
    # Login de administradores (vista personalizada)
    path('auth/admin-login/', AdminUserLoginView.as_view(), name='admin-login'),
    
    # Logout de administradores
    path('auth/admin-logout/', AdminUserLogoutView.as_view(), name='admin-logout'),
    
    # Token de autenticación estándar de DRF (opcional)
    path('auth/token/', CustomObtainAuthToken.as_view(), name='api_token_auth'),
]

# ============================================================================
# DOCUMENTACIÓN DE ENDPOINTS DISPONIBLES
# ============================================================================

"""
ENDPOINTS GENERADOS AUTOMÁTICAMENTE POR EL ROUTER:

Pre-Registro de Usuarios:
- GET    /api/users/pre-register/                    - Lista todos los pre-registros
- POST   /api/users/pre-register/                    - Crear nuevo pre-registro
- GET    /api/users/pre-register/{id}/               - Detalle de pre-registro
- PUT    /api/users/pre-register/{id}/               - Actualizar pre-registro completo
- PATCH  /api/users/pre-register/{id}/               - Actualizar pre-registro parcial
- DELETE /api/users/pre-register/{id}/               - Eliminar pre-registro
- POST   /api/users/pre-register/verify-phone/       - Verificar si existe preregistro por teléfono
- POST   /api/users/pre-register/approve/            - Aprobar múltiples pre-registros

Usuarios Finales:
- GET    /api/users/customers/                       - Lista todos los usuarios
- POST   /api/users/customers/                       - Crear nuevo usuario
- GET    /api/users/customers/{id}/                  - Detalle de usuario
- PUT    /api/users/customers/{id}/                  - Actualizar usuario completo
- PATCH  /api/users/customers/{id}/                  - Actualizar usuario parcial
- DELETE /api/users/customers/{id}/                  - Eliminar usuario
- POST   /api/users/customers/deactivate-multiple/   - Desactivar múltiples usuarios

Administradores:
- GET    /api/users/admins/                          - Lista todos los administradores
- POST   /api/users/admins/                          - Crear nuevo administrador
- GET    /api/users/admins/{id}/                     - Detalle de administrador
- PUT    /api/users/admins/{id}/                     - Actualizar administrador completo
- PATCH  /api/users/admins/{id}/                     - Actualizar administrador parcial
- DELETE /api/users/admins/{id}/                     - Eliminar administrador
- POST   /api/users/admins/change-password/          - Cambiar contraseña

Verificación de Teléfono:
- GET    /api/users/phone-verification/              - Lista verificaciones de teléfono
- POST   /api/users/phone-verification/              - Crear nueva verificación
- GET    /api/users/phone-verification/{id}/         - Detalle de verificación
- PUT    /api/users/phone-verification/{id}/         - Actualizar verificación completa
- PATCH  /api/users/phone-verification/{id}/         - Actualizar verificación parcial
- DELETE /api/users/phone-verification/{id}/         - Eliminar verificación
- POST   /api/users/phone-verification/send/         - Enviar código de verificación
- POST   /api/users/phone-verification/verify/       - Verificar código

Autenticación:
- POST   /api/users/auth/admin-login/                - Login de administradores
- POST   /api/users/auth/admin-logout/               - Logout de administradores
- POST   /api/users/auth/token/                      - Obtener token estándar DRF

FILTROS Y BÚSQUEDAS DISPONIBLES:

Pre-Registros:
- Filtros: ?status=pending&gender=M&age=25
- Búsqueda: ?search=Juan (busca en nombre, apellido, teléfono)
- Ordenamiento: ?ordering=-created_at (por fecha desc)

Usuarios:
- Filtros: ?gender=F&is_active=true&poverty_level=6
- Búsqueda: ?search=Maria (busca en nombre, apellido, teléfono)
- Ordenamiento: ?ordering=first_name (por nombre asc)

Administradores:
- Filtros: ?is_active=true&is_superuser=false
- Búsqueda: ?search=admin (busca en username, nombre, apellido)
- Ordenamiento: ?ordering=-last_login (por último acceso desc)

Verificación de Teléfono:
- Filtros: ?purpose=login&channel=sms&user={uuid}
- Búsqueda: ?search=Juan (busca en datos del usuario)
- Ordenamiento: ?ordering=-expires_at (por expiración desc)

PAGINACIÓN:
Todos los endpoints soportan paginación automática con los parámetros:
- ?page=1&page_size=20 (página 1, 20 elementos por página)
- Los valores por defecto se configuran en settings.py

EJEMPLOS DE USO:

1. Crear pre-registro:
POST /api/users/pre-register/
{
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone_number": "+52 1234567890",
    "age": 25,
    "gender": "M",
    "privacy_policy_accepted": true
}

2. Verificar teléfono:
POST /api/users/pre-register/verify-phone/
{
    "phone_number": "+52 1234567890"
}

3. Login de administrador:
POST /api/users/auth/admin-login/
{
    "username": "admin",
    "password": "password123"
}

4. Filtrar usuarios por género:
GET /api/users/customers/?gender=F&is_active=true

5. Buscar administradores:
GET /api/users/admins/?search=juan&ordering=-created_at
"""
