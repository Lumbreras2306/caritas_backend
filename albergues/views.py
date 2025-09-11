# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count

# DRF Spectacular imports para documentación automática
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Location, Hostel, HostelReservation
from .serializers import (
    LocationSerializer, HostelSerializer, HostelCreateSerializer,
    HostelReservationSerializer, HostelReservationUpdateSerializer,
    BulkStatusUpdateSerializer
)

# ============================================================================
# VIEWSETS PARA UBICACIONES
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Locations'],
        summary="Lista ubicaciones",
        description="Obtiene lista paginada de ubicaciones geográficas con filtros y búsqueda",
        parameters=[
            OpenApiParameter(name='city', type=OpenApiTypes.STR, description='Filtrar por ciudad'),
            OpenApiParameter(name='state', type=OpenApiTypes.STR, description='Filtrar por estado'),
            OpenApiParameter(name='country', type=OpenApiTypes.STR, description='Filtrar por país'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en dirección, ciudad, estado, landmarks'),
        ]
    ),
    create=extend_schema(
        tags=['Locations'],
        summary="Crear ubicación",
        description="Crea una nueva ubicación geográfica",
        examples=[
            OpenApiExample(
                'Ubicación ejemplo',
                value={
                    "latitude": 19.4326,
                    "longitude": -99.1332,
                    "address": "Calle Principal 123",
                    "city": "Ciudad de México",
                    "state": "Ciudad de México",
                    "zip_code": "01000",
                    "landmarks": "Cerca del metro Zócalo"
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Locations'], summary="Detalle de ubicación"),
    update=extend_schema(tags=['Locations'], summary="Actualizar ubicación"),
    partial_update=extend_schema(tags=['Locations'], summary="Actualizar ubicación parcial"),
    destroy=extend_schema(tags=['Locations'], summary="Eliminar ubicación"),
)
class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de ubicaciones geográficas.
    
    Las ubicaciones incluyen coordenadas GPS, direcciones y puntos de referencia
    para facilitar la localización de albergues y servicios.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'state', 'country']
    search_fields = ['address', 'city', 'state', 'landmarks']
    ordering_fields = ['created_at', 'city', 'state']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Personalizar creación de ubicación"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de ubicación"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

# ============================================================================
# VIEWSETS PARA ALBERGUES
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Hostels'],
        summary="Lista albergues",
        description="Obtiene lista paginada de albergues con información de ubicación y capacidad",
        parameters=[
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Filtrar por estado activo'),
            OpenApiParameter(name='location__city', type=OpenApiTypes.STR, description='Filtrar por ciudad'),
            OpenApiParameter(name='location__state', type=OpenApiTypes.STR, description='Filtrar por estado'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre, teléfono, dirección'),
        ]
    ),
    create=extend_schema(
        tags=['Hostels'],
        summary="Crear albergue",
        description="Crea un nuevo albergue con su ubicación",
        examples=[
            OpenApiExample(
                'Albergue ejemplo',
                value={
                    "name": "Casa de Acogida San José",
                    "phone": "+52811908593",
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
            )
        ]
    ),
    retrieve=extend_schema(tags=['Hostels'], summary="Detalle de albergue"),
    update=extend_schema(tags=['Hostels'], summary="Actualizar albergue"),
    partial_update=extend_schema(tags=['Hostels'], summary="Actualizar albergue parcial"),
    destroy=extend_schema(tags=['Hostels'], summary="Eliminar albergue"),
)
class HostelViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de albergues.
    
    Los albergues son centros de acogida que proporcionan alojamiento
    temporal a personas en situación vulnerable.
    """
    queryset = Hostel.objects.select_related('location').all()
    serializer_class = HostelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'location__city', 'location__state']
    search_fields = ['name', 'phone', 'location__address', 'location__city']
    ordering_fields = ['created_at', 'name', 'location__city']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Usar serializer diferente para creación"""
        if self.action == 'create':
            return HostelCreateSerializer
        return HostelSerializer

    def perform_create(self, serializer):
        """Personalizar creación de albergue"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de albergue"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @extend_schema(
        tags=['Hostels'],
        summary="Buscar albergues cercanos",
        description="Busca albergues cercanos a una ubicación específica usando coordenadas GPS",
        parameters=[
            OpenApiParameter(name='lat', type=OpenApiTypes.FLOAT, required=True, description='Latitud de referencia'),
            OpenApiParameter(name='lng', type=OpenApiTypes.FLOAT, required=True, description='Longitud de referencia'),
            OpenApiParameter(name='radius', type=OpenApiTypes.FLOAT, description='Radio de búsqueda en kilómetros (default: 10)')
        ],
        responses={
            200: OpenApiResponse(description="Albergues cercanos encontrados"),
            400: OpenApiResponse(description="Parámetros de ubicación inválidos"),
        },
        # examples=[
        #     OpenApiExample(
        #         'Búsqueda cercana',
        #         description='Buscar albergues en un radio de 5km',
        #         request_only=False,
        #         parameter_only={'lat': 19.4326, 'lng': -99.1332, 'radius': 5}
        #     )
        # ]
    )
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Buscar albergues cercanos a una ubicación."""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))
        
        if not lat or not lng:
            return Response(
                {'error': 'Se requieren parámetros lat y lng'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
            
            # Filtro simple por proximidad (en una implementación real usarías PostGIS)
            lat_range = radius / 111.0  # Aproximación: 1 grado ≈ 111 km
            lng_range = radius / (111.0 * abs(float(lat)))  # Ajustar por latitud
            
            hostels = self.get_queryset().filter(
                location__latitude__range=(lat - lat_range, lat + lat_range),
                location__longitude__range=(lng - lng_range, lng + lng_range),
                is_active=True
            )
            
            serializer = self.get_serializer(hostels, many=True)
            return Response({
                'search_center': {'lat': lat, 'lng': lng},
                'radius_km': radius,
                'count': hostels.count(),
                'results': serializer.data
            })
            
        except ValueError:
            return Response(
                {'error': 'Coordenadas inválidas'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        tags=['Hostels'],
        summary="Consultar disponibilidad",
        description="Consulta la disponibilidad de espacios en un albergue para una fecha específica",
        parameters=[
            OpenApiParameter(name='date', type=OpenApiTypes.DATE, required=True, description='Fecha para consultar (YYYY-MM-DD)')
        ],
        responses={
            200: OpenApiResponse(description="Disponibilidad obtenida exitosamente"),
            400: OpenApiResponse(description="Formato de fecha inválido"),
            404: OpenApiResponse(description="Albergue no encontrado"),
        },
        # examples=[
        #     OpenApiExample(
        #         'Consulta disponibilidad',
        #         description='Verificar espacios disponibles para una fecha',
        #         parameter_only={'date': '2024-01-15'},
        #         request_only=False
        #     )
        # ]
    )
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Consultar disponibilidad de un albergue."""
        hostel = self.get_object()
        date_param = request.query_params.get('date')
        
        if not date_param:
            return Response(
                {'error': 'Se requiere parámetro date (YYYY-MM-DD)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            check_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            
            # Calcular reservas confirmadas para esa fecha
            reservations = HostelReservation.objects.filter(
                hostel=hostel,
                arrival_date=check_date,
                status='confirmed'
            )
            
            reserved_men = reservations.aggregate(
                total=Sum('men_quantity')
            )['total'] or 0
            
            reserved_women = reservations.aggregate(
                total=Sum('women_quantity')
            )['total'] or 0
            
            # Calcular disponibilidad
            available_men = max(0, (hostel.men_capacity or 0) - reserved_men)
            available_women = max(0, (hostel.women_capacity or 0) - reserved_women)
            
            return Response({
                'hostel': {
                    'id': hostel.id,
                    'name': hostel.name,
                    'location': hostel.get_formatted_address()
                },
                'date': check_date,
                'capacity': {
                    'men': hostel.men_capacity or 0,
                    'women': hostel.women_capacity or 0,
                    'total': hostel.get_total_capacity()
                },
                'reserved': {
                    'men': reserved_men,
                    'women': reserved_women,
                    'total': reserved_men + reserved_women
                },
                'available': {
                    'men': available_men,
                    'women': available_women,
                    'total': available_men + available_women
                }
            })
            
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

# ============================================================================
# VIEWSETS PARA RESERVAS DE ALBERGUES
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Hostel Reservations'],
        summary="Lista reservas de alojamiento",
        description="Obtiene lista paginada de reservas de alojamiento en albergues",
        parameters=[
            OpenApiParameter(name='status', type=OpenApiTypes.STR, enum=['pending', 'confirmed', 'cancelled', 'rejected', 'completed'], description='Filtrar por estado'),
            OpenApiParameter(name='type', type=OpenApiTypes.STR, enum=['individual', 'group'], description='Filtrar por tipo'),
            OpenApiParameter(name='hostel', type=OpenApiTypes.UUID, description='Filtrar por albergue'),
            OpenApiParameter(name='arrival_date', type=OpenApiTypes.DATE, description='Filtrar por fecha de llegada'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre del usuario y albergue'),
        ]
    ),
    create=extend_schema(
        tags=['Hostel Reservations'],
        summary="Crear reserva de alojamiento",
        description="Crea una nueva reserva de alojamiento en un albergue",
        examples=[
            OpenApiExample(
                'Reserva individual',
                value={
                    "user": "123e4567-e89b-12d3-a456-426614174000",
                    "hostel": "123e4567-e89b-12d3-a456-426614174001",
                    "type": "individual",
                    "arrival_date": "2024-01-15",
                    "men_quantity": 1,
                    "women_quantity": 0
                }
            ),
            OpenApiExample(
                'Reserva grupal',
                value={
                    "user": "123e4567-e89b-12d3-a456-426614174000",
                    "hostel": "123e4567-e89b-12d3-a456-426614174001",
                    "type": "group",
                    "arrival_date": "2024-01-20",
                    "men_quantity": 3,
                    "women_quantity": 2
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Hostel Reservations'], summary="Detalle de reserva de alojamiento"),
    update=extend_schema(tags=['Hostel Reservations'], summary="Actualizar reserva de alojamiento"),
    partial_update=extend_schema(tags=['Hostel Reservations'], summary="Actualizar reserva parcial"),
    destroy=extend_schema(tags=['Hostel Reservations'], summary="Eliminar reserva de alojamiento"),
)
class HostelReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reservas de alojamiento en albergues.
    
    Las reservas permiten a los usuarios solicitar espacios de alojamiento
    en albergues para fechas específicas, con gestión de capacidad por género.
    """
    queryset = HostelReservation.objects.select_related('user', 'hostel', 'hostel__location').all()
    serializer_class = HostelReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type', 'hostel', 'arrival_date']
    search_fields = ['user__first_name', 'user__last_name', 'hostel__name']
    ordering_fields = ['created_at', 'arrival_date', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Usar serializer diferente para actualización de status"""
        if self.action in ['partial_update', 'update'] and 'status' in self.request.data:
            return HostelReservationUpdateSerializer
        return HostelReservationSerializer

    def perform_create(self, serializer):
        """Personalizar creación de reserva"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de reserva"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @extend_schema(
        tags=['Hostel Reservations'],
        summary="Mis reservas de alojamiento",
        description="Obtiene las reservas de alojamiento del usuario actual. Los administradores ven todas las reservas.",
        parameters=[
            OpenApiParameter(name='status', type=OpenApiTypes.STR, enum=['pending', 'confirmed', 'cancelled', 'completed'], description='Filtrar por estado'),
            OpenApiParameter(name='arrival_date', type=OpenApiTypes.DATE, description='Filtrar por fecha de llegada'),
        ]
    )
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """Obtener las reservas del usuario actual."""
        # Si es administrador, puede ver todas, sino solo las suyas
        if hasattr(request.user, 'is_staff') and request.user.is_staff:
            reservations = self.get_queryset()
        else:
            reservations = self.get_queryset().filter(user=request.user)
        
        # Aplicar filtros de la URL
        filtered_reservations = self.filter_queryset(reservations)
        
        page = self.paginate_queryset(filtered_reservations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_reservations, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Hostel Reservations'],
        summary="Actualizar múltiples estados",
        description="Actualiza el estado de múltiples reservas de alojamiento de forma masiva",
        request=BulkStatusUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Reservas actualizadas exitosamente"),
            400: OpenApiResponse(description="Datos inválidos"),
            500: OpenApiResponse(description="Error interno del servidor"),
        },
        examples=[
            OpenApiExample(
                'Confirmar reservas',
                value={
                    "reservation_ids": [
                        "123e4567-e89b-12d3-a456-426614174000",
                        "123e4567-e89b-12d3-a456-426614174001"
                    ],
                    "status": "confirmed"
                }
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def update_status(self, request):
        """Actualizar el estado de múltiples reservas."""
        reservation_ids = request.data.get('reservation_ids', [])
        new_status = request.data.get('status')
        
        if not reservation_ids or not new_status:
            return Response(
                {'error': 'Se requieren reservation_ids y status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el status sea válido
        valid_statuses = [choice[0] for choice in HostelReservation.ReservationStatus.choices]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Status inválido. Opciones: {valid_statuses}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                reservations = HostelReservation.objects.filter(id__in=reservation_ids)
                updated_count = reservations.update(
                    status=new_status,
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
                return Response({
                    'message': f'{updated_count} reservas actualizadas exitosamente',
                    'updated_count': updated_count,
                    'new_status': new_status,
                    'updated_reservations': list(reservations.values_list('id', flat=True))
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error al actualizar reservas: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
