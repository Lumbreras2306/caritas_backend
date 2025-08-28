# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LocationViewSet,
    HostelViewSet,
    HostelReservationViewSet
)

# ============================================================================
# CONFIGURACIÓN DE ROUTERS
# ============================================================================

# Router principal para ViewSets de albergues
router = DefaultRouter()

# Registrar ViewSets en el router
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'hostels', HostelViewSet, basename='hostel')
router.register(r'reservations', HostelReservationViewSet, basename='reservation')

# ============================================================================
# PATRONES DE URL
# ============================================================================

urlpatterns = [
    # URLs generadas automáticamente por el router
    path('', include(router.urls)),
]

# ============================================================================
# DOCUMENTACIÓN DE ENDPOINTS DISPONIBLES
# ============================================================================

"""
ENDPOINTS GENERADOS AUTOMÁTICAMENTE POR EL ROUTER:

Ubicaciones:
- GET    /api/albergues/locations/                    - Lista todas las ubicaciones
- POST   /api/albergues/locations/                    - Crear nueva ubicación
- GET    /api/albergues/locations/{id}/               - Detalle de ubicación
- PUT    /api/albergues/locations/{id}/               - Actualizar ubicación completa
- PATCH  /api/albergues/locations/{id}/               - Actualizar ubicación parcial
- DELETE /api/albergues/locations/{id}/               - Eliminar ubicación

Albergues:
- GET    /api/albergues/hostels/                      - Lista todos los albergues
- POST   /api/albergues/hostels/                      - Crear nuevo albergue
- GET    /api/albergues/hostels/{id}/                 - Detalle de albergue
- PUT    /api/albergues/hostels/{id}/                 - Actualizar albergue completo
- PATCH  /api/albergues/hostels/{id}/                 - Actualizar albergue parcial
- DELETE /api/albergues/hostels/{id}/                 - Eliminar albergue
- GET    /api/albergues/hostels/nearby/               - Buscar albergues cercanos
- GET    /api/albergues/hostels/{id}/availability/    - Consultar disponibilidad

Reservas:
- GET    /api/albergues/reservations/                 - Lista todas las reservas
- POST   /api/albergues/reservations/                 - Crear nueva reserva
- GET    /api/albergues/reservations/{id}/            - Detalle de reserva
- PUT    /api/albergues/reservations/{id}/            - Actualizar reserva completa
- PATCH  /api/albergues/reservations/{id}/            - Actualizar reserva parcial
- DELETE /api/albergues/reservations/{id}/            - Eliminar reserva
- GET    /api/albergues/reservations/my-reservations/ - Mis reservas
- POST   /api/albergues/reservations/update-status/   - Actualizar múltiples estados

FILTROS Y BÚSQUEDAS DISPONIBLES:

Ubicaciones:
- Filtros: ?city=CDMX&state=Ciudad de México&country=México
- Búsqueda: ?search=Centro (busca en dirección, ciudad, estado, landmarks)
- Ordenamiento: ?ordering=-created_at

Albergues:
- Filtros: ?is_active=true&location__city=CDMX
- Búsqueda: ?search=Casa (busca en nombre, teléfono, dirección)
- Ordenamiento: ?ordering=name

Reservas:
- Filtros: ?status=confirmed&arrival_date=2024-01-15&hostel={uuid}
- Búsqueda: ?search=Juan (busca en nombre del usuario y albergue)
- Ordenamiento: ?ordering=arrival_date

EJEMPLOS DE USO:

1. Crear albergue con ubicación:
POST /api/albergues/hostels/
{
    "name": "Casa de Acogida San José",
    "phone": "+52 1234567890",
    "men_capacity": 20,
    "women_capacity": 15,
    "location": {
        "latitude": 19.4326,
        "longitude": -99.1332,
        "address": "Calle Principal 123",
        "city": "Ciudad de México",
        "state": "Ciudad de México",
        "zip_code": "01000"
    }
}

2. Buscar albergues cercanos:
GET /api/albergues/hostels/nearby/?lat=19.4326&lng=-99.1332&radius=5

3. Consultar disponibilidad:
GET /api/albergues/hostels/{id}/availability/?date=2024-01-15

4. Crear reserva:
POST /api/albergues/reservations/
{
    "user": "{user_uuid}",
    "hostel": "{hostel_uuid}",
    "type": "individual",
    "arrival_date": "2024-01-15",
    "men_quantity": 1,
    "women_quantity": 0
}

5. Actualizar múltiples reservas:
POST /api/albergues/reservations/update-status/
{
    "reservation_ids": ["uuid1", "uuid2"],
    "status": "confirmed"
}
"""
