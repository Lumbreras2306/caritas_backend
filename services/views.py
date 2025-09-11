# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, timedelta

# DRF Spectacular imports para documentación automática
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Service, ServiceSchedule, HostelService, ReservationService
from .serializers import (
    ServiceSerializer, ServiceScheduleSerializer, HostelServiceSerializer,
    ReservationServiceSerializer, ReservationServiceUpdateSerializer,
    ReservationServiceDetailSerializer, BulkServiceReservationStatusUpdateSerializer
)

# ============================================================================
# VIEWSETS PARA SERVICIOS
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Services'],
        summary="Lista servicios",
        description="Obtiene lista paginada de servicios disponibles (comida, aseo, etc.)",
        parameters=[
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Filtrar por estado activo'),
            OpenApiParameter(name='reservation_type', type=OpenApiTypes.STR, enum=['individual', 'group'], description='Filtrar por tipo de reserva'),
            OpenApiParameter(name='needs_approval', type=OpenApiTypes.BOOL, description='Filtrar por necesidad de aprobación'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre y descripción'),
        ]
    ),
    create=extend_schema(
        tags=['Services'],
        summary="Crear servicio",
        description="Crea un nuevo servicio disponible en el sistema",
        examples=[
            OpenApiExample(
                'Servicio de comida',
                value={
                    "name": "Servicio de Comidas",
                    "description": "Comidas balanceadas para huéspedes",
                    "price": 50.00,
                    "reservation_type": "individual",
                    "needs_approval": False,
                    "max_time": 60
                }
            ),
            OpenApiExample(
                'Servicio de aseo',
                value={
                    "name": "Servicio de Duchas",
                    "description": "Acceso a duchas y baños",
                    "price": 15.00,
                    "reservation_type": "individual",
                    "needs_approval": False,
                    "max_time": 30
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Services'], summary="Detalle de servicio"),
    update=extend_schema(tags=['Services'], summary="Actualizar servicio"),
    partial_update=extend_schema(tags=['Services'], summary="Actualizar servicio parcial"),
    destroy=extend_schema(tags=['Services'], summary="Eliminar servicio"),
)
class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de servicios.
    
    Los servicios son actividades o recursos que los albergues pueden
    ofrecer a los usuarios (comida, duchas, lavandería, etc.).
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

    @extend_schema(
        tags=['Services'],
        summary="Estadísticas de servicios",
        description="Obtiene estadísticas generales de todos los servicios del sistema",
        responses={
            200: OpenApiResponse(description="Estadísticas obtenidas exitosamente"),
            401: OpenApiResponse(description="No autorizado"),
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Estadísticas generales de servicios."""
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
        
        # Estadísticas de reservas
        total_reservations = ReservationService.objects.count()
        reservations_by_status = ReservationService.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return Response({
            'services': {
                'total_services': total_services,
                'active_services': active_services,
                'inactive_services': total_services - active_services,
                'needs_approval_count': needs_approval_count,
                'auto_approval_count': total_services - needs_approval_count
            },
            'pricing': price_stats,
            'by_reservation_type': list(by_reservation_type),
            'reservations': {
                'total_reservations': total_reservations,
                'by_status': list(reservations_by_status)
            }
        })

# ============================================================================
# VIEWSETS PARA HORARIOS DE SERVICIOS
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Service Schedules'],
        summary="Lista horarios de servicios",
        description="Obtiene lista paginada de horarios para servicios",
        parameters=[
            OpenApiParameter(name='day_of_week', type=OpenApiTypes.INT, description='Filtrar por día de la semana (0=Lunes, 6=Domingo)'),
            OpenApiParameter(name='is_available', type=OpenApiTypes.BOOL, description='Filtrar por disponibilidad'),
        ]
    ),
    create=extend_schema(
        tags=['Service Schedules'],
        summary="Crear horario de servicio",
        description="Crea un nuevo horario para servicios",
        examples=[
            OpenApiExample(
                'Horario de desayuno',
                value={
                    "day_of_week": 1,
                    "start_time": "07:00",
                    "end_time": "09:00",
                    "is_available": True
                }
            ),
            OpenApiExample(
                'Horario de duchas',
                value={
                    "day_of_week": 0,
                    "start_time": "06:00",
                    "end_time": "20:00",
                    "is_available": True
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Service Schedules'], summary="Detalle de horario"),
    update=extend_schema(tags=['Service Schedules'], summary="Actualizar horario"),
    partial_update=extend_schema(tags=['Service Schedules'], summary="Actualizar horario parcial"),
    destroy=extend_schema(tags=['Service Schedules'], summary="Eliminar horario"),
)
class ServiceScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de horarios de servicios.
    
    Los horarios definen cuándo están disponibles los servicios
    durante la semana, con horarios específicos por día.
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

@extend_schema_view(
    list=extend_schema(
        tags=['Hostel Services'],
        summary="Lista servicios de albergues",
        description="Obtiene lista de servicios asignados a albergues específicos",
        parameters=[
            OpenApiParameter(name='hostel', type=OpenApiTypes.UUID, description='Filtrar por albergue'),
            OpenApiParameter(name='service', type=OpenApiTypes.UUID, description='Filtrar por servicio'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Filtrar por estado activo'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre del albergue y servicio'),
        ]
    ),
    create=extend_schema(
        tags=['Hostel Services'],
        summary="Asignar servicio a albergue",
        description="Asigna un servicio específico a un albergue",
        examples=[
            OpenApiExample(
                'Asignar servicio de comida',
                value={
                    "hostel": "123e4567-e89b-12d3-a456-426614174000",
                    "service": "123e4567-e89b-12d3-a456-426614174001",
                    "schedule": "123e4567-e89b-12d3-a456-426614174002",
                    "is_active": True
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Hostel Services'], summary="Detalle de servicio de albergue"),
    update=extend_schema(tags=['Hostel Services'], summary="Actualizar servicio de albergue"),
    partial_update=extend_schema(tags=['Hostel Services'], summary="Actualizar servicio parcial"),
    destroy=extend_schema(tags=['Hostel Services'], summary="Eliminar servicio de albergue"),
)
class HostelServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de servicios de albergues.
    
    Permite asignar servicios específicos a albergues,
    definiendo qué servicios están disponibles en cada ubicación.
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

    @extend_schema(
        tags=['Hostel Services'],
        summary="Servicios por albergue",
        description="Obtiene servicios agrupados por albergue o de un albergue específico",
        parameters=[
            OpenApiParameter(name='hostel', type=OpenApiTypes.UUID, description='ID del albergue específico (opcional)'),
        ],
        responses={
            200: OpenApiResponse(description="Servicios obtenidos exitosamente"),
        },
        # examples=[
        #     OpenApiExample(
        #         'Consulta por albergue',
        #         description='Ver servicios de un albergue específico',
        #         parameter_only={'hostel': '123e4567-e89b-12d3-a456-426614174000'},
        #         request_only=False
        #     )
        # ]
    )
    @action(detail=False, methods=['get'])
    def by_hostel(self, request):
        """Servicios agrupados por albergue."""
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
                    'needs_approval': hostel_service.service.needs_approval,
                    'max_time': hostel_service.service.max_time
                })
            
            return Response({
                'hostels': dict(services_by_hostel),
                'total_hostels': len(services_by_hostel),
                'total_services': hostel_services.count()
            })

# ============================================================================
# VIEWSETS PARA RESERVAS DE SERVICIOS
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Service Reservations'],
        summary="Lista reservas de servicios",
        description="Obtiene lista paginada de reservas de servicios (comida, duchas, etc.)",
        parameters=[
            OpenApiParameter(name='status', type=OpenApiTypes.STR, enum=['pending', 'confirmed', 'cancelled', 'rejected', 'completed', 'in_progress'], description='Filtrar por estado'),
            OpenApiParameter(name='type', type=OpenApiTypes.STR, enum=['individual', 'group'], description='Filtrar por tipo'),
            OpenApiParameter(name='service__hostel', type=OpenApiTypes.UUID, description='Filtrar por albergue'),
            OpenApiParameter(name='service__service', type=OpenApiTypes.UUID, description='Filtrar por servicio'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre del usuario, servicio y albergue'),
        ]
    ),
    create=extend_schema(
        tags=['Service Reservations'],
        summary="Crear reserva de servicio",
        description="Crea una nueva reserva de servicio para un usuario",
        examples=[
            OpenApiExample(
                'Reserva de comida individual',
                value={
                    "user": "123e4567-e89b-12d3-a456-426614174000",
                    "service": "123e4567-e89b-12d3-a456-426614174001",
                    "type": "individual",
                    "datetime_reserved": "2024-01-15T12:00:00Z",
                    "men_quantity": 1,
                    "women_quantity": 0
                }
            ),
            OpenApiExample(
                'Reserva de duchas grupal',
                value={
                    "user": "123e4567-e89b-12d3-a456-426614174000",
                    "service": "123e4567-e89b-12d3-a456-426614174002",
                    "type": "group",
                    "datetime_reserved": "2024-01-15T08:00:00Z",
                    "men_quantity": 2,
                    "women_quantity": 3
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Service Reservations'], summary="Detalle de reserva de servicio"),
    update=extend_schema(tags=['Service Reservations'], summary="Actualizar reserva de servicio"),
    partial_update=extend_schema(tags=['Service Reservations'], summary="Actualizar reserva parcial"),
    destroy=extend_schema(tags=['Service Reservations'], summary="Eliminar reserva de servicio"),
)
class ReservationServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reservas de servicios.
    
    Las reservas de servicios permiten a los usuarios solicitar
    acceso a servicios específicos en horarios determinados.
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

    @extend_schema(
        tags=['Service Reservations'],
        summary="Mis reservas de servicios",
        description="Obtiene las reservas de servicios del usuario actual. Los administradores ven todas las reservas.",
        parameters=[
            OpenApiParameter(name='status', type=OpenApiTypes.STR, enum=['pending', 'confirmed', 'cancelled', 'completed'], description='Filtrar por estado'),
            OpenApiParameter(name='datetime_reserved', type=OpenApiTypes.DATETIME, description='Filtrar por fecha/hora de reserva'),
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
        tags=['Service Reservations'],
        summary="Reservas próximas",
        description="Obtiene reservas de servicios en las próximas 24 horas",
        parameters=[
            OpenApiParameter(name='hours', type=OpenApiTypes.INT, description='Horas hacia adelante para buscar (default: 24)'),
        ]
    )
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Reservas próximas (en las próximas 24 horas)."""
        hours = int(request.query_params.get('hours', 24))
        now = timezone.now()
        future_time = now + timedelta(hours=hours)
        
        upcoming_reservations = self.get_queryset().filter(
            datetime_reserved__gte=now,
            datetime_reserved__lte=future_time,
            status__in=['confirmed', 'pending']
        ).order_by('datetime_reserved')
        
        serializer = self.get_serializer(upcoming_reservations, many=True)
        return Response({
            'count': upcoming_reservations.count(),
            'time_range': {
                'from': now,
                'to': future_time,
                'hours': hours
            },
            'reservations': serializer.data
        })

    @extend_schema(
        tags=['Service Reservations'],
        summary="Actualizar múltiples estados",
        description="Actualiza el estado de múltiples reservas de servicios de forma masiva",
        request=BulkServiceReservationStatusUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Reservas actualizadas exitosamente"),
            400: OpenApiResponse(description="Datos inválidos"),
            500: OpenApiResponse(description="Error interno del servidor"),
        },
        examples=[
            OpenApiExample(
                'Confirmar reservas de comida',
                value={
                    "reservation_ids": [
                        "123e4567-e89b-12d3-a456-426614174000",
                        "123e4567-e89b-12d3-a456-426614174001"
                    ],
                    "status": "confirmed"
                }
            ),
            OpenApiExample(
                'Marcar en progreso',
                value={
                    "reservation_ids": [
                        "123e4567-e89b-12d3-a456-426614174002"
                    ],
                    "status": "in_progress"
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
                    'message': f'{updated_count} reservas de servicios actualizadas exitosamente',
                    'updated_count': updated_count,
                    'new_status': new_status,
                    'updated_reservations': list(reservations.values_list('id', flat=True))
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error al actualizar reservas: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
