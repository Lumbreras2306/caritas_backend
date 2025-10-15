# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count, F
from users.permissions import IsAdminUser, CustomUserHostelAccess, CustomUserReservationAccess

from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, 
    OpenApiResponse, OpenApiExample, OpenApiTypes
)

from .models import Location, Hostel, HostelReservation
from .serializers import (
    LocationSerializer, HostelSerializer, HostelCreateSerializer,
    HostelReservationSerializer, HostelReservationUpdateSerializer,
    BulkStatusUpdateSerializer, ErrorResponseSerializer, SuccessResponseSerializer,
    BulkOperationResponseSerializer, HostelAvailabilityResponseSerializer,
    NearbyHostelsResponseSerializer
)

# ============================================================================
# VIEWSETS PARA UBICACIONES
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Albergues'],
        summary="Lista ubicaciones",
        description="Obtiene lista paginada de ubicaciones geográficas con filtros y búsqueda",
        parameters=[
            OpenApiParameter(name='city', type=OpenApiTypes.STR, description='Filtrar por ciudad'),
            OpenApiParameter(name='state', type=OpenApiTypes.STR, description='Filtrar por estado'),
            OpenApiParameter(name='country', type=OpenApiTypes.STR, description='Filtrar por país'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en dirección, ciudad, estado, landmarks'),
        ],
        responses={
            200: LocationSerializer(many=True),
            401: ErrorResponseSerializer,
        }
    ),
    create=extend_schema(
        tags=['Albergues'],
        summary="Crear ubicación",
        description="Crea una nueva ubicación geográfica",
        request=LocationSerializer,
        responses={
            201: LocationSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
        },
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
                },
                request_only=True,
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Albergues'], 
        summary="Detalle de ubicación",
        responses={200: LocationSerializer, 404: ErrorResponseSerializer}
    ),
    update=extend_schema(
        tags=['Albergues'], 
        summary="Actualizar ubicación",
        responses={200: LocationSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=['Albergues'], 
        summary="Actualizar ubicación parcial",
        responses={200: LocationSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        tags=['Albergues'], 
        summary="Eliminar ubicación",
        responses={204: None, 404: ErrorResponseSerializer}
    ),
)
class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de ubicaciones geográficas.
    
    Las ubicaciones incluyen coordenadas GPS, direcciones y puntos de referencia
    para facilitar la localización de albergues y servicios.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'state', 'country']
    search_fields = ['address', 'city', 'state', 'landmarks']
    ordering_fields = ['created_at', 'city', 'state']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user)
        return instance

# ============================================================================
# VIEWSETS PARA ALBERGUES
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Albergues'],
        summary="Lista albergues",
        description="Obtiene lista paginada de albergues con información de ubicación y capacidad",
        parameters=[
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Filtrar por estado activo'),
            OpenApiParameter(name='location__city', type=OpenApiTypes.STR, description='Filtrar por ciudad'),
            OpenApiParameter(name='location__state', type=OpenApiTypes.STR, description='Filtrar por estado'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre, teléfono, dirección'),
        ],
        responses={
            200: HostelSerializer(many=True),
            401: ErrorResponseSerializer,
        }
    ),
    create=extend_schema(
        tags=['Albergues'],
        summary="Crear albergue",
        description="Crea un nuevo albergue con su ubicación",
        request=HostelCreateSerializer,
        responses={
            201: HostelSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
        },
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
                },
                request_only=True,
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Albergues'], 
        summary="Detalle de albergue",
        responses={200: HostelSerializer, 404: ErrorResponseSerializer}
    ),
    update=extend_schema(
        tags=['Albergues'], 
        summary="Actualizar albergue",
        responses={200: HostelSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=['Albergues'], 
        summary="Actualizar albergue parcial",
        responses={200: HostelSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        tags=['Albergues'], 
        summary="Eliminar albergue",
        responses={204: None, 404: ErrorResponseSerializer}
    ),
)
class HostelViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de albergues.
    
    Los albergues son centros de acogida que proporcionan alojamiento
    temporal a personas en situación vulnerable.
    """
    queryset = Hostel.objects.select_related('location').all()
    serializer_class = HostelSerializer
    permission_classes = [CustomUserHostelAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'location__city', 'location__state']
    search_fields = ['name', 'phone', 'location__address', 'location__city']
    ordering_fields = ['created_at', 'name', 'location__city']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return HostelCreateSerializer
        return HostelSerializer

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @extend_schema(
        tags=['Albergues'],
        summary="Buscar albergues cercanos",
        description="Busca albergues cercanos a una ubicación específica usando coordenadas GPS",
        parameters=[
            OpenApiParameter(
                name='lat', 
                type=OpenApiTypes.FLOAT, 
                required=True, 
                description='Latitud de referencia',
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='lng', 
                type=OpenApiTypes.FLOAT, 
                required=True, 
                description='Longitud de referencia',
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='radius', 
                type=OpenApiTypes.FLOAT, 
                description='Radio de búsqueda en kilómetros (default: 10)',
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: NearbyHostelsResponseSerializer,
            400: ErrorResponseSerializer,
        }
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
            
            lat_range = radius / 111.0
            lng_range = radius / (111.0 * abs(float(lat)))
            
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
        tags=['Albergues'],
        summary="Consultar disponibilidad",
        description="Consulta la disponibilidad de espacios en un albergue para una fecha específica",
        parameters=[
            OpenApiParameter(
                name='date', 
                type=OpenApiTypes.DATE, 
                required=True, 
                description='Fecha para consultar (YYYY-MM-DD)',
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: HostelAvailabilityResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        }
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
            
            reservations = HostelReservation.objects.filter(
                hostel=hostel,
                arrival_date=check_date,
                status='confirmed'
            )
            
            reserved_men = reservations.aggregate(total=Sum('men_quantity'))['total'] or 0
            reserved_women = reservations.aggregate(total=Sum('women_quantity'))['total'] or 0
            
            men_total = hostel.men_capacity or 0
            women_total = hostel.women_capacity or 0
            men_current = hostel.current_men_capacity or 0
            women_current = hostel.current_women_capacity or 0
            
            available_men = max(0, men_total - men_current - reserved_men)
            available_women = max(0, women_total - women_current - reserved_women)
            
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
                'current_occupancy': {
                    'men': men_current,
                    'women': women_current,
                    'total': men_current + women_current
                },
                'reserved_for_date': {
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
        tags=['Albergues'],
        summary="Lista reservas de alojamiento",
        description="Obtiene lista paginada de reservas de alojamiento en albergues",
        parameters=[
            OpenApiParameter(
                name='status', 
                type=OpenApiTypes.STR, 
                enum=['pending', 'confirmed', 'cancelled', 'rejected', 'completed'], 
                description='Filtrar por estado'
            ),
            OpenApiParameter(
                name='type', 
                type=OpenApiTypes.STR, 
                enum=['individual', 'group'], 
                description='Filtrar por tipo'
            ),
            OpenApiParameter(name='hostel', type=OpenApiTypes.UUID, description='Filtrar por albergue'),
            OpenApiParameter(name='arrival_date', type=OpenApiTypes.DATE, description='Filtrar por fecha de llegada'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre del usuario y albergue'),
        ],
        responses={
            200: HostelReservationSerializer(many=True),
            401: ErrorResponseSerializer,
        }
    ),
    create=extend_schema(
        tags=['Albergues'],
        summary="Crear reserva de alojamiento",
        description="Crea una nueva reserva de alojamiento en un albergue",
        request=HostelReservationSerializer,
        responses={
            201: HostelReservationSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
        },
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
                },
                request_only=True,
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
                },
                request_only=True,
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Albergues'], 
        summary="Detalle de reserva de alojamiento",
        responses={200: HostelReservationSerializer, 404: ErrorResponseSerializer}
    ),
    update=extend_schema(
        tags=['Albergues'], 
        summary="Actualizar reserva de alojamiento",
        responses={200: HostelReservationSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=['Albergues'], 
        summary="Actualizar reserva parcial",
        responses={200: HostelReservationSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        tags=['Albergues'], 
        summary="Eliminar reserva de alojamiento",
        responses={204: None, 404: ErrorResponseSerializer}
    ),
)
class HostelReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reservas de alojamiento en albergues.
    
    Las reservas permiten a los usuarios solicitar espacios de alojamiento
    en albergues para fechas específicas, con gestión de capacidad por género.
    """
    queryset = HostelReservation.objects.select_related('user', 'hostel', 'hostel__location').all()
    serializer_class = HostelReservationSerializer
    permission_classes = [CustomUserReservationAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type', 'hostel', 'arrival_date']
    search_fields = ['user__first_name', 'user__last_name', 'hostel__name']
    ordering_fields = ['created_at', 'arrival_date', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['partial_update', 'update'] and 'status' in self.request.data:
            return HostelReservationUpdateSerializer
        return HostelReservationSerializer

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @extend_schema(
        tags=['Albergues'],
        summary="Mis reservas de alojamiento",
        description="Obtiene las reservas de alojamiento del usuario actual. Los administradores ven todas las reservas.",
        parameters=[
            OpenApiParameter(
                name='status', 
                type=OpenApiTypes.STR, 
                enum=['pending', 'confirmed', 'cancelled', 'completed'], 
                description='Filtrar por estado'
            ),
            OpenApiParameter(name='arrival_date', type=OpenApiTypes.DATE, description='Filtrar por fecha de llegada'),
        ],
        responses={
            200: HostelReservationSerializer(many=True),
            401: ErrorResponseSerializer,
        }
    )
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """Obtener las reservas del usuario actual."""
        if hasattr(request.user, 'is_staff') and request.user.is_staff:
            reservations = self.get_queryset()
        else:
            reservations = self.get_queryset().filter(user=request.user)
        
        filtered_reservations = self.filter_queryset(reservations)
        
        page = self.paginate_queryset(filtered_reservations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(filtered_reservations, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Albergues'],
        summary="Actualizar múltiples estados",
        description="Actualiza el estado de múltiples reservas de alojamiento de forma masiva",
        request=BulkStatusUpdateSerializer,
        responses={
            200: BulkOperationResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
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
                },
                request_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def update_status(self, request):
        """Actualizar el estado de múltiples reservas."""
        serializer = BulkStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        reservation_ids = serializer.validated_data['reservation_ids']
        new_status = serializer.validated_data['status']
        
        try:
            with transaction.atomic():
                reservations = HostelReservation.objects.filter(id__in=reservation_ids).select_related('hostel')
                
                updated_count = 0
                updated_reservations = []
                
                for reservation in reservations:
                    old_status = reservation.status
                    reservation.status = new_status
                    reservation.updated_by = request.user
                    reservation.updated_at = timezone.now()
                    reservation.save()
                    
                    self._update_hostel_capacity_for_reservation(reservation, old_status, new_status)
                    
                    updated_count += 1
                    updated_reservations.append(str(reservation.id))
                
                return Response({
                    'message': f'{updated_count} reservas actualizadas exitosamente',
                    'updated_count': updated_count,
                    'new_status': new_status,
                    'updated_reservations': updated_reservations
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error al actualizar reservas: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _update_hostel_capacity_for_reservation(self, reservation, old_status, new_status):
        hostel = reservation.hostel
        
        if old_status != 'confirmed' and new_status == 'confirmed':
            self._add_to_current_capacity(hostel, reservation)
        
        elif old_status == 'confirmed' and new_status in ['cancelled', 'rejected', 'completed']:
            self._remove_from_current_capacity(hostel, reservation)
    
    def _add_to_current_capacity(self, hostel, reservation):
        men_quantity = reservation.men_quantity or 0
        women_quantity = reservation.women_quantity or 0
        hostel.add_to_current_capacity(men_quantity, women_quantity)
    
    def _remove_from_current_capacity(self, hostel, reservation):
        men_quantity = reservation.men_quantity or 0
        women_quantity = reservation.women_quantity or 0
        hostel.remove_from_current_capacity(men_quantity, women_quantity)
