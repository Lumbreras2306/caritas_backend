# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, timedelta

from .models import Service, ServiceSchedule, HostelService, ReservationService
from .serializers import (
    ServiceSerializer, ServiceScheduleSerializer, HostelServiceSerializer,
    ReservationServiceSerializer, ReservationServiceUpdateSerializer,
    ReservationServiceDetailSerializer
)

# ============================================================================
# VIEWSETS PARA SERVICIOS
# ============================================================================

class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de servicios.
    
    Endpoints:
    - GET /api/services/services/ - Lista todos los servicios
    - POST /api/services/services/ - Crear nuevo servicio
    - GET /api/services/services/{id}/ - Detalle de servicio
    - PUT/PATCH /api/services/services/{id}/ - Actualizar servicio
    - DELETE /api/services/services/{id}/ - Eliminar servicio
    - GET /api/services/services/statistics/ - Estadísticas de servicios
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'reservation_type', 'needs_approval']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'price', 'max_time']
    ordering = ['name']

    def perform_create(self, serializer):
        """Personalizar creación de servicio"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de servicio"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estadísticas generales de servicios.
        
        GET /api/services/services/statistics/
        """
        services = self.get_queryset()
        
        # Estadísticas básicas
        total_services = services.count()
        active_services = services.filter(is_active=True).count()
        
        # Precios
        from django.db.models import Min, Max
        price_stats = services.aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        # Por tipo de reserva
        by_reservation_type = services.values('reservation_type').annotate(
            count=Count('id')
        ).order_by('reservation_type')
        
        # Servicios que necesitan aprobación
        needs_approval_count = services.filter(needs_approval=True).count()
        
        return Response({
            'total_services': total_services,
            'active_services': active_services,
            'inactive_services': total_services - active_services,
            'price_statistics': price_stats,
            'by_reservation_type': list(by_reservation_type),
            'needs_approval_count': needs_approval_count,
            'auto_approval_count': total_services - needs_approval_count
        })

# ============================================================================
# VIEWSETS PARA HORARIOS DE SERVICIOS
# ============================================================================

class ServiceScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de horarios de servicios.
    
    Endpoints:
    - GET /api/services/schedules/ - Lista todos los horarios
    - POST /api/services/schedules/ - Crear nuevo horario
    - GET /api/services/schedules/{id}/ - Detalle de horario
    - PUT/PATCH /api/services/schedules/{id}/ - Actualizar horario
    - DELETE /api/services/schedules/{id}/ - Eliminar horario
    """
    queryset = ServiceSchedule.objects.all()
    serializer_class = ServiceScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['day_of_week', 'is_available']
    search_fields = []
    ordering_fields = ['created_at', 'day_of_week', 'start_time']
    ordering = ['day_of_week', 'start_time']

    def perform_create(self, serializer):
        """Personalizar creación de horario"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de horario"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

# ============================================================================
# VIEWSETS PARA SERVICIOS DE ALBERGUES
# ============================================================================

class HostelServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de servicios de albergues.
    
    Endpoints:
    - GET /api/services/hostel-services/ - Lista todos los servicios de albergues
    - POST /api/services/hostel-services/ - Crear nuevo servicio de albergue
    - GET /api/services/hostel-services/{id}/ - Detalle de servicio de albergue
    - PUT/PATCH /api/services/hostel-services/{id}/ - Actualizar servicio de albergue
    - DELETE /api/services/hostel-services/{id}/ - Eliminar servicio de albergue
    - GET /api/services/hostel-services/by-hostel/ - Servicios por albergue
    """
    queryset = HostelService.objects.select_related('hostel', 'service', 'schedule').all()
    serializer_class = HostelServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hostel', 'service', 'is_active']
    search_fields = ['hostel__name', 'service__name', 'service__description']
    ordering_fields = ['created_at', 'hostel__name', 'service__name']
    ordering = ['hostel__name', 'service__name']

    def perform_create(self, serializer):
        """Personalizar creación de servicio de albergue"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de servicio de albergue"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @action(detail=False, methods=['get'])
    def by_hostel(self, request):
        """
        Servicios agrupados por albergue.
        
        GET /api/services/hostel-services/by-hostel/?hostel={uuid}
        """
        hostel_id = request.query_params.get('hostel')
        
        if hostel_id:
            # Servicios de un albergue específico
            hostel_services = self.get_queryset().filter(hostel_id=hostel_id, is_active=True)
            serializer = self.get_serializer(hostel_services, many=True)
            
            return Response({
                'hostel_id': hostel_id,
                'count': hostel_services.count(),
                'services': serializer.data
            })
        else:
            # Todos los servicios agrupados por albergue
            from collections import defaultdict
            services_by_hostel = defaultdict(list)
            
            hostel_services = self.get_queryset().filter(is_active=True)
            
            for hostel_service in hostel_services:
                services_by_hostel[hostel_service.hostel.name].append({
                    'id': hostel_service.id,
                    'service_name': hostel_service.service.name,
                    'service_price': float(hostel_service.service.price),
                    'needs_approval': hostel_service.service.needs_approval
                })
            
            return Response({
                'hostels': dict(services_by_hostel),
                'total_hostels': len(services_by_hostel),
                'total_services': hostel_services.count()
            })

# ============================================================================
# VIEWSETS PARA RESERVAS DE SERVICIOS
# ============================================================================

class ReservationServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reservas de servicios.
    
    Endpoints:
    - GET /api/services/reservations/ - Lista todas las reservas
    - POST /api/services/reservations/ - Crear nueva reserva
    - GET /api/services/reservations/{id}/ - Detalle de reserva
    - PUT/PATCH /api/services/reservations/{id}/ - Actualizar reserva
    - DELETE /api/services/reservations/{id}/ - Eliminar reserva
    - POST /api/services/reservations/update-status/ - Actualizar múltiples estados
    - GET /api/services/reservations/my-reservations/ - Mis reservas
    - GET /api/services/reservations/upcoming/ - Reservas próximas
    """
    queryset = ReservationService.objects.select_related(
        'user', 'service__hostel', 'service__service'
    ).all()
    serializer_class = ReservationServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type', 'service__hostel', 'service__service']
    search_fields = ['user__first_name', 'user__last_name', 'service__service__name', 'service__hostel__name']
    ordering_fields = ['created_at', 'datetime_reserved', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Usar serializer diferente según la acción"""
        if self.action == 'retrieve':
            return ReservationServiceDetailSerializer
        elif self.action in ['partial_update', 'update'] and 'status' in self.request.data:
            return ReservationServiceUpdateSerializer
        return ReservationServiceSerializer

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
        
        GET /api/services/reservations/my-reservations/
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

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Reservas próximas (en las próximas 24 horas).
        
        GET /api/services/reservations/upcoming/
        """
        now = timezone.now()
        tomorrow = now + timedelta(hours=24)
        
        upcoming_reservations = self.get_queryset().filter(
            datetime_reserved__gte=now,
            datetime_reserved__lte=tomorrow,
            status__in=['confirmed', 'pending']
        ).order_by('datetime_reserved')
        
        serializer = self.get_serializer(upcoming_reservations, many=True)
        return Response({
            'count': upcoming_reservations.count(),
            'time_range': {
                'from': now,
                'to': tomorrow
            },
            'reservations': serializer.data
        })

    @action(detail=False, methods=['post'])
    def update_status(self, request):
        """
        Actualizar el estado de múltiples reservas.
        
        POST /api/services/reservations/update-status/
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
        valid_statuses = [choice[0] for choice in ReservationService.ReservationStatus.choices]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Status inválido. Opciones: {valid_statuses}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                reservations = ReservationService.objects.filter(id__in=reservation_ids)
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
