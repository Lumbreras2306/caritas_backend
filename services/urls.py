# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ServiceViewSet,
    ServiceScheduleViewSet,
    HostelServiceViewSet,
    ReservationServiceViewSet
)

# ============================================================================
# CONFIGURACIÓN DE ROUTERS
# ============================================================================

# Router principal para ViewSets de servicios
router = DefaultRouter()

# Registrar ViewSets en el router
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'schedules', ServiceScheduleViewSet, basename='schedule')
router.register(r'hostel-services', HostelServiceViewSet, basename='hostelservice')
router.register(r'reservations', ReservationServiceViewSet, basename='reservation')

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

Servicios:
- GET    /api/services/services/                      - Lista todos los servicios
- POST   /api/services/services/                      - Crear nuevo servicio
- GET    /api/services/services/{id}/                 - Detalle de servicio
- PUT    /api/services/services/{id}/                 - Actualizar servicio completo
- PATCH  /api/services/services/{id}/                 - Actualizar servicio parcial
- DELETE /api/services/services/{id}/                 - Eliminar servicio
- GET    /api/services/services/statistics/           - Estadísticas de servicios

Horarios:
- GET    /api/services/schedules/                     - Lista todos los horarios
- POST   /api/services/schedules/                     - Crear nuevo horario
- GET    /api/services/schedules/{id}/                - Detalle de horario
- PUT    /api/services/schedules/{id}/                - Actualizar horario completo
- PATCH  /api/services/schedules/{id}/                - Actualizar horario parcial
- DELETE /api/services/schedules/{id}/                - Eliminar horario

Servicios de Albergues:
- GET    /api/services/hostel-services/               - Lista servicios de albergues
- POST   /api/services/hostel-services/               - Crear servicio de albergue
- GET    /api/services/hostel-services/{id}/          - Detalle de servicio de albergue
- PUT    /api/services/hostel-services/{id}/          - Actualizar servicio completo
- PATCH  /api/services/hostel-services/{id}/          - Actualizar servicio parcial
- DELETE /api/services/hostel-services/{id}/          - Eliminar servicio de albergue
- GET    /api/services/hostel-services/by-hostel/     - Servicios por albergue

Reservas:
- GET    /api/services/reservations/                  - Lista todas las reservas
- POST   /api/services/reservations/                  - Crear nueva reserva
- GET    /api/services/reservations/{id}/             - Detalle de reserva
- PUT    /api/services/reservations/{id}/             - Actualizar reserva completa
- PATCH  /api/services/reservations/{id}/             - Actualizar reserva parcial
- DELETE /api/services/reservations/{id}/             - Eliminar reserva
- GET    /api/services/reservations/my-reservations/  - Mis reservas
- GET    /api/services/reservations/upcoming/         - Reservas próximas
- POST   /api/services/reservations/update-status/    - Actualizar múltiples estados

FILTROS Y BÚSQUEDAS DISPONIBLES:

Servicios:
- Filtros: ?is_active=true&reservation_type=individual&needs_approval=false
- Búsqueda: ?search=Comida (busca en nombre, descripción)
- Ordenamiento: ?ordering=name,price

Horarios:
- Filtros: ?day_of_week=1&is_available=true
- Ordenamiento: ?ordering=day_of_week,start_time

Servicios de Albergues:
- Filtros: ?hostel={uuid}&service={uuid}&is_active=true
- Búsqueda: ?search=Cocina (busca en nombre del albergue, servicio)
- Ordenamiento: ?ordering=hostel__name,service__name

Reservas:
- Filtros: ?status=confirmed&service__hostel={uuid}&service__service={uuid}
- Búsqueda: ?search=Juan (busca en nombre del usuario, servicio, albergue)
- Ordenamiento: ?ordering=datetime_reserved,-created_at

EJEMPLOS DE USO:

1. Crear servicio:
POST /api/services/services/
{
    "name": "Servicio de Comidas",
    "description": "Comidas balanceadas para huéspedes",
    "price": 50.00,
    "reservation_type": "individual",
    "needs_approval": false,
    "max_time": 60
}

2. Crear horario:
POST /api/services/schedules/
{
    "day_of_week": 1,
    "start_time": "07:00",
    "end_time": "20:00",
    "is_available": true
}

3. Asignar servicio a albergue:
POST /api/services/hostel-services/
{
    "hostel": "{hostel_uuid}",
    "service": "{service_uuid}",
    "schedule": "{schedule_uuid}",
    "is_active": true
}

4. Crear reserva de servicio:
POST /api/services/reservations/
{
    "user": "{user_uuid}",
    "service": "{hostel_service_uuid}",
    "type": "individual",
    "datetime_reserved": "2024-01-15T12:00:00Z",
    "men_quantity": 1,
    "women_quantity": 0
}

5. Ver servicios por albergue:
GET /api/services/hostel-services/by-hostel/?hostel={uuid}

6. Ver reservas próximas:
GET /api/services/reservations/upcoming/

7. Actualizar múltiples reservas:
POST /api/services/reservations/update-status/
{
    "reservation_ids": ["uuid1", "uuid2"],
    "status": "confirmed"
}

8. Ver estadísticas de servicios:
GET /api/services/services/statistics/
"""
