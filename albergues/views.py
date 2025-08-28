# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count

from .models import Location, Hostel, HostelReservation
from .serializers import (
    LocationSerializer, HostelSerializer, HostelCreateSerializer,
    HostelReservationSerializer, HostelReservationUpdateSerializer
)

# ============================================================================
# VIEWSETS PARA UBICACIONES
# ============================================================================

class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de ubicaciones geográficas.
    
    Endpoints:
    - GET /api/albergues/locations/ - Lista todas las ubicaciones
    - POST /api/albergues/locations/ - Crear nueva ubicación
    - GET /api/albergues/locations/{id}/ - Detalle de ubicación
    - PUT/PATCH /api/albergues/locations/{id}/ - Actualizar ubicación
    - DELETE /api/albergues/locations/{id}/ - Eliminar ubicación
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

class HostelViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de albergues.
    
    Endpoints:
    - GET /api/albergues/hostels/ - Lista todos los albergues
    - POST /api/albergues/hostels/ - Crear nuevo albergue
    - GET /api/albergues/hostels/{id}/ - Detalle de albergue
    - PUT/PATCH /api/albergues/hostels/{id}/ - Actualizar albergue
    - DELETE /api/albergues/hostels/{id}/ - Eliminar albergue
    - GET /api/albergues/hostels/nearby/ - Buscar albergues cercanos
    - GET /api/albergues/hostels/{id}/availability/ - Consultar disponibilidad
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

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Buscar albergues cercanos a una ubicación.
        
        GET /api/albergues/hostels/nearby/?lat=19.4326&lng=-99.1332&radius=10
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))  # Radio en km por defecto
        
        if not lat or not lng:
            return Response(
                {'error': 'Se requieren parámetros lat y lng'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
            
            # Filtro simple por proximidad (en una implementación real usarías PostGIS)
            # Por ahora filtramos por un rango aproximado
            lat_range = radius / 111.0  # Aproximación: 1 grado ≈ 111 km
            lng_range = radius / (111.0 * abs(float(lat)))  # Ajustar por latitud
            
            hostels = self.get_queryset().filter(
                location__latitude__range=(lat - lat_range, lat + lat_range),
                location__longitude__range=(lng - lng_range, lng + lng_range),
                is_active=True
            )
            
            serializer = self.get_serializer(hostels, many=True)
            return Response({
                'count': hostels.count(),
                'results': serializer.data
            })
            
        except ValueError:
            return Response(
                {'error': 'Coordenadas inválidas'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Consultar disponibilidad de un albergue.
        
        GET /api/albergues/hostels/{id}/availability/?date=2024-01-15
        """
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
                'hostel': hostel.name,
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

class HostelReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reservas de albergues.
    
    Endpoints:
    - GET /api/albergues/reservations/ - Lista todas las reservas
    - POST /api/albergues/reservations/ - Crear nueva reserva
    - GET /api/albergues/reservations/{id}/ - Detalle de reserva
    - PUT/PATCH /api/albergues/reservations/{id}/ - Actualizar reserva
    - DELETE /api/albergues/reservations/{id}/ - Eliminar reserva
    - POST /api/albergues/reservations/update-status/ - Actualizar múltiples estados
    - GET /api/albergues/reservations/my-reservations/ - Mis reservas
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

    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """
        Obtener las reservas del usuario actual.
        
        GET /api/albergues/reservations/my-reservations/
        """
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

    @action(detail=False, methods=['post'])
    def update_status(self, request):
        """
        Actualizar el estado de múltiples reservas.
        
        POST /api/albergues/reservations/update-status/
        Body: {
            "reservation_ids": ["uuid1", "uuid2"],
            "status": "confirmed"
        }
        """
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
                    'new_status': new_status
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error al actualizar reservas: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )