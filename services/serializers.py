# serializers.py
from rest_framework import serializers
from typing import Dict, Any, Optional
from .models import Service, ServiceSchedule, HostelService, ReservationService
from django.utils import timezone
from datetime import datetime, timedelta

# ============================================================================
# SERIALIZERS DE RESPUESTAS ESTÁNDAR
# ============================================================================

class ErrorResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de error estándar"""
    error = serializers.CharField(help_text="Mensaje de error")
    detail = serializers.CharField(required=False, help_text="Detalle adicional del error")

class SuccessResponseSerializer(serializers.Serializer):
    """Serializer para respuestas exitosas estándar"""
    message = serializers.CharField(help_text="Mensaje de éxito")
    data = serializers.DictField(required=False, help_text="Datos adicionales")

class BulkOperationResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de operaciones masivas"""
    message = serializers.CharField(help_text="Mensaje descriptivo de la operación")
    updated_count = serializers.IntegerField(help_text="Cantidad de registros actualizados")

# ============================================================================
# SERIALIZERS PARA SERVICIOS
# ============================================================================

class ServiceSerializer(serializers.ModelSerializer):
    """Serializer para servicios"""
    reservation_type_display = serializers.CharField(source='get_reservation_type_display', read_only=True)
    max_time_hours = serializers.SerializerMethodField()
    total_hostels = serializers.SerializerMethodField()
    total_reservations = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'price', 'is_active', 'reservation_type',
            'reservation_type_display', 'needs_approval', 'max_time', 'max_time_hours',
            'total_hostels', 'total_reservations',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reservation_type_display', 'max_time_hours', 
            'total_hostels', 'total_reservations',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_max_time_hours(self, obj) -> Optional[str]:
        """Convertir minutos a horas para mejor legibilidad"""
        if obj.max_time:
            hours = obj.max_time // 60
            minutes = obj.max_time % 60
            if hours > 0 and minutes > 0:
                return f"{hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h"
            else:
                return f"{minutes}m"
        return None
    
    def get_total_hostels(self, obj) -> int:
        """Número de albergues que ofrecen este servicio"""
        return obj.hostelservice_set.filter(is_active=True).count()
    
    def get_total_reservations(self, obj) -> int:
        """Número total de reservas de este servicio"""
        return ReservationService.objects.filter(service__service=obj).count()
    
    def validate_max_time(self, value):
        """Validar que el tiempo máximo sea razonable"""
        if value <= 0:
            raise serializers.ValidationError("El tiempo máximo debe ser mayor a 0 minutos")
        if value > 1440:  # 24 horas
            raise serializers.ValidationError("El tiempo máximo no puede ser mayor a 24 horas (1440 minutos)")
        return value

# ============================================================================
# SERIALIZERS PARA HORARIOS DE SERVICIOS
# ============================================================================

class ServiceScheduleSerializer(serializers.ModelSerializer):
    """Serializer para horarios de servicios"""
    day_name = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ServiceSchedule
        fields = [
            'id', 'day_of_week', 'day_name', 'start_time', 'end_time', 
            'duration_hours', 'is_available',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'day_name', 'duration_hours',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_day_name(self, obj) -> str:
        """Nombre del día de la semana"""
        days = {
            0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
            4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
        }
        return days.get(obj.day_of_week, 'Desconocido')
    
    def get_duration_hours(self, obj) -> Optional[float]:
        """Duración del horario en horas"""
        if obj.start_time and obj.end_time:
            start_datetime = datetime.combine(datetime.today(), obj.start_time)
            end_datetime = datetime.combine(datetime.today(), obj.end_time)
            
            # Si el horario termina al día siguiente
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
            
            duration = end_datetime - start_datetime
            hours = duration.total_seconds() / 3600
            return round(hours, 2)
        return None
    
    def validate_day_of_week(self, value):
        """Validar que el día de la semana esté en rango válido"""
        if value < 0 or value > 6:
            raise serializers.ValidationError("El día de la semana debe estar entre 0 (lunes) y 6 (domingo)")
        return value
    
    def validate(self, attrs):
        """Validar que la hora de inicio sea antes que la de fin"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                "La hora de inicio debe ser anterior a la hora de fin"
            )
        
        return attrs

# ============================================================================
# SERIALIZERS PARA SERVICIOS DE ALBERGUES
# ============================================================================

class HostelServiceSerializer(serializers.ModelSerializer):
    """Serializer para servicios de albergues"""
    hostel_name = serializers.CharField(source='hostel.name', read_only=True)
    hostel_location = serializers.CharField(source='hostel.get_formatted_address', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_description = serializers.CharField(source='service.description', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    service_max_time = serializers.IntegerField(source='service.max_time', read_only=True)
    service_needs_approval = serializers.BooleanField(source='service.needs_approval', read_only=True)
    schedule_data = ServiceScheduleSerializer(source='schedule', read_only=True)
    total_reservations = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = HostelService
        fields = [
            'id', 'hostel', 'hostel_name', 'hostel_location',
            'service', 'service_name', 'service_description', 'service_price', 
            'service_max_time', 'service_needs_approval',
            'schedule', 'schedule_data', 'is_active', 'total_reservations',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'hostel_name', 'hostel_location', 'service_name', 'service_description',
            'service_price', 'service_max_time', 'service_needs_approval', 'schedule_data',
            'total_reservations', 'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_total_reservations(self, obj) -> int:
        """Número total de reservas para este servicio de albergue"""
        return obj.reservationservice_set.count()

# ============================================================================
# SERIALIZERS PARA RESERVAS DE SERVICIOS
# ============================================================================

class ReservationServiceSerializer(serializers.ModelSerializer):
    """Serializer para reservas de servicios"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    service_name = serializers.CharField(source='service.service.name', read_only=True)
    service_price = serializers.DecimalField(source='service.service.price', max_digits=10, decimal_places=2, read_only=True)
    hostel_name = serializers.CharField(source='service.hostel.name', read_only=True)
    hostel_location = serializers.CharField(source='service.hostel.get_formatted_address', read_only=True)
    total_people = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    is_expired = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ReservationService
        fields = [
            'id', 'user', 'user_name', 'user_phone',
            'service', 'service_name', 'service_price', 'hostel_name', 'hostel_location',
            'status', 'status_display', 'type', 'type_display',
            'men_quantity', 'women_quantity', 'total_people',
            'datetime_reserved', 'end_datetime_reserved', 'duration_minutes',
            'is_expired', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'user_phone', 'service_name', 'service_price',
            'hostel_name', 'hostel_location', 'status_display', 'type_display',
            'total_people', 'end_datetime_reserved', 'duration_minutes', 'is_expired',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_total_people(self, obj) -> int:
        """Total de personas en la reserva"""
        men = obj.men_quantity or 0
        women = obj.women_quantity or 0
        return men + women
    
    def get_duration_minutes(self, obj) -> Optional[int]:
        """Duración de la reserva en minutos"""
        if obj.datetime_reserved and obj.end_datetime_reserved:
            duration = obj.end_datetime_reserved - obj.datetime_reserved
            return int(duration.total_seconds() / 60)
        return None
    
    def get_is_expired(self, obj) -> bool:
        """Verificar si la reserva ya expiró"""
        if obj.end_datetime_reserved:
            return timezone.now() > obj.end_datetime_reserved
        return False

class BulkServiceReservationStatusUpdateSerializer(serializers.Serializer):
    """Serializer para actualización masiva de estados de reservas de servicios"""
    reservation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Lista de IDs de reservas a actualizar"
    )
    status = serializers.ChoiceField(
        choices=[
            ('pending', 'Pendiente'),
            ('confirmed', 'Confirmada'),
            ('cancelled', 'Cancelada'),
            ('rejected', 'Rechazada'),
            ('completed', 'Completada'),
            ('in_progress', 'En Progreso'),
        ],
        help_text="Nuevo estado para las reservas"
    )
    
    def validate_reservation_ids(self, value):
        """Validar que la lista no esté vacía"""
        if not value:
            raise serializers.ValidationError("La lista de IDs no puede estar vacía")
        return value
    
    def validate(self, attrs):
        """Validaciones para la reserva"""
        men_quantity = attrs.get('men_quantity')
        women_quantity = attrs.get('women_quantity')
        
        # Al menos una cantidad debe ser especificada
        if not men_quantity and not women_quantity:
            raise serializers.ValidationError(
                "Debe especificar al menos una cantidad (hombres o mujeres)"
            )
        
        return attrs
    
    def validate_datetime_reserved(self, value):
        """Validar que la fecha/hora de reserva sea en el futuro"""
        if value <= timezone.now():
            raise serializers.ValidationError(
                "La fecha y hora de reserva debe ser en el futuro"
            )
        return value

class ReservationServiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar solo el status de reservas"""
    
    class Meta:
        model = ReservationService
        fields = ['status']
    
    def update(self, instance, validated_data):
        """Actualizar solo el status y registrar quién lo modificó"""
        instance.status = validated_data.get('status', instance.status)
        
        # Registrar quién modificó la reserva si hay usuario en contexto
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            instance.updated_by = request.user
        
        instance.save()
        return instance

class ReservationServiceDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para reservas con toda la información"""
    user_data = serializers.SerializerMethodField()
    service_data = HostelServiceSerializer(source='service', read_only=True)
    total_people = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    is_expired = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = ReservationService
        fields = [
            'id', 'user', 'user_data', 'service', 'service_data',
            'status', 'status_display', 'type', 'type_display',
            'men_quantity', 'women_quantity', 'total_people',
            'datetime_reserved', 'end_datetime_reserved', 'duration_minutes',
            'is_expired', 'created_by_name', 'updated_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_data', 'service_data', 'status_display', 'type_display',
            'total_people', 'end_datetime_reserved', 'duration_minutes', 'is_expired',
            'created_by_name', 'updated_by_name', 'created_at', 'updated_at'
        ]
    
    def get_user_data(self, obj) -> Dict[str, Any]:
        """Datos básicos del usuario"""
        return {
            'id': obj.user.id,
            'full_name': obj.user.get_full_name(),
            'phone_number': obj.user.phone_number,
        } if hasattr(obj.user, 'phone_number') else {
            'id': obj.user.id,
            'full_name': obj.user.get_full_name(),
            'username': obj.user.username,
        }
    
    def get_total_people(self, obj) -> int:
        """Total de personas en la reserva"""
        men = obj.men_quantity or 0
        women = obj.women_quantity or 0
        return men + women
    
    def get_duration_minutes(self, obj) -> Optional[int]:
        """Duración de la reserva en minutos"""
        if obj.datetime_reserved and obj.end_datetime_reserved:
            duration = obj.end_datetime_reserved - obj.datetime_reserved
            return int(duration.total_seconds() / 60)
        return None
    
    def get_is_expired(self, obj) -> bool:
        """Verificar si la reserva ya expiró"""
        if obj.end_datetime_reserved:
            return timezone.now() > obj.end_datetime_reserved
        return False

class BulkServiceReservationStatusUpdateSerializer(serializers.Serializer):
    """Serializer para actualización masiva de estados de reservas de servicios"""
    reservation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Lista de IDs de reservas a actualizar"
    )
    status = serializers.ChoiceField(
        choices=[
            ('pending', 'Pendiente'),
            ('confirmed', 'Confirmada'),
            ('cancelled', 'Cancelada'),
            ('rejected', 'Rechazada'),
            ('completed', 'Completada'),
            ('in_progress', 'En Progreso'),
        ],
        help_text="Nuevo estado para las reservas"
    )
    
    def validate_reservation_ids(self, value):
        """Validar que la lista no esté vacía"""
        if not value:
            raise serializers.ValidationError("La lista de IDs no puede estar vacía")
        return value
