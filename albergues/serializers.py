# serializers.py
from rest_framework import serializers
from typing import Dict, Any, Tuple
from .models import Location, Hostel, HostelReservation

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
    new_status = serializers.CharField(required=False, help_text="Nuevo estado aplicado")
    updated_reservations = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="Lista de IDs actualizados"
    )

# ============================================================================
# SERIALIZERS PARA UBICACIONES
# ============================================================================

class LocationSerializer(serializers.ModelSerializer):
    """Serializer para ubicaciones geográficas"""
    coordinates = serializers.SerializerMethodField(help_text="Tupla de coordenadas (lat, lng)")
    google_maps_url = serializers.SerializerMethodField(help_text="URL directa a Google Maps")
    formatted_address = serializers.SerializerMethodField(help_text="Dirección completa formateada")
    
    class Meta:
        model = Location
        fields = [
            'id', 'latitude', 'longitude', 'address', 'city', 'state', 
            'country', 'zip_code', 'timezone', 'landmarks',
            'coordinates', 'google_maps_url', 'formatted_address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'coordinates', 'google_maps_url', 'formatted_address', 'created_at', 'updated_at']
    
    def get_coordinates(self, obj) -> Tuple[float, float]:
        return obj.get_coordinates()
    
    def get_google_maps_url(self, obj) -> str:
        return obj.get_google_maps_url()
    
    def get_formatted_address(self, obj) -> str:
        return obj.get_formatted_address()

# ============================================================================
# SERIALIZERS PARA ALBERGUES
# ============================================================================

class HostelSerializer(serializers.ModelSerializer):
    """Serializer para albergues"""
    location_data = LocationSerializer(source='location', read_only=True)
    total_capacity = serializers.SerializerMethodField(help_text="Capacidad total del albergue (hombres + mujeres)")
    current_capacity = serializers.SerializerMethodField(help_text="Capacidad actual utilizada (hombres + mujeres)")
    available_capacity = serializers.SerializerMethodField(help_text="Capacidad disponible por género y total")
    coordinates = serializers.SerializerMethodField(help_text="Coordenadas GPS del albergue")
    formatted_address = serializers.SerializerMethodField(help_text="Dirección completa del albergue")
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    current_men_capacity = serializers.IntegerField(
        read_only=True, 
        help_text="Capacidad actual de hombres utilizada"
    )
    current_women_capacity = serializers.IntegerField(
        read_only=True, 
        help_text="Capacidad actual de mujeres utilizada"
    )
    
    class Meta:
        model = Hostel
        fields = [
            'id', 'name', 'phone', 'men_capacity', 'current_men_capacity', 
            'women_capacity', 'current_women_capacity', 'is_active', 'image_url',
            'location', 'location_data', 'total_capacity', 'current_capacity', 
            'available_capacity', 'coordinates', 'formatted_address',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'location_data', 'total_capacity', 'current_capacity', 
            'available_capacity', 'coordinates', 'formatted_address',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_total_capacity(self, obj) -> int:
        men_cap = obj.men_capacity or 0
        women_cap = obj.women_capacity or 0
        return men_cap + women_cap
    
    def get_current_capacity(self, obj) -> int:
        men_current = obj.current_men_capacity or 0
        women_current = obj.current_women_capacity or 0
        return men_current + women_current
    
    def get_available_capacity(self, obj) -> dict:
        men_total = obj.men_capacity or 0
        women_total = obj.women_capacity or 0
        men_current = obj.current_men_capacity or 0
        women_current = obj.current_women_capacity or 0
        
        return {
            'men': max(0, men_total - men_current),
            'women': max(0, women_total - women_current),
            'total': max(0, (men_total + women_total) - (men_current + women_current))
        }
    
    def get_coordinates(self, obj) -> Tuple[float, float]:
        return obj.get_coordinates()
    
    def get_formatted_address(self, obj) -> str:
        return obj.get_formatted_address()
    
    def validate(self, attrs):
        men_capacity = attrs.get('men_capacity')
        women_capacity = attrs.get('women_capacity')
        
        if not men_capacity and not women_capacity:
            raise serializers.ValidationError(
                "Debe especificar al menos una capacidad (hombres o mujeres)"
            )
        
        return attrs

class HostelCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear albergues con ubicación"""
    location = LocationSerializer()
    
    class Meta:
        model = Hostel
        fields = [
            'name', 'phone', 'men_capacity', 'current_men_capacity', 
            'women_capacity', 'current_women_capacity', 'is_active', 'image_url', 'location'
        ]
    
    def create(self, validated_data):
        location_data = validated_data.pop('location')
        location = Location.objects.create(**location_data)
        hostel = Hostel.objects.create(location=location, **validated_data)
        return hostel
    
    def validate(self, attrs):
        men_capacity = attrs.get('men_capacity')
        women_capacity = attrs.get('women_capacity')
        
        if not men_capacity and not women_capacity:
            raise serializers.ValidationError(
                "Debe especificar al menos una capacidad (hombres o mujeres)"
            )
        
        return attrs

class HostelAvailabilityResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de disponibilidad de albergue"""
    hostel = serializers.DictField(help_text="Información del albergue")
    date = serializers.DateField(help_text="Fecha consultada")
    capacity = serializers.DictField(help_text="Capacidad total del albergue")
    current_occupancy = serializers.DictField(help_text="Ocupación actual")
    reserved_for_date = serializers.DictField(help_text="Reservas para la fecha específica")
    available = serializers.DictField(help_text="Disponibilidad por género")

class NearbyHostelsResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de búsqueda de albergues cercanos"""
    search_center = serializers.DictField(help_text="Centro de búsqueda (lat, lng)")
    radius_km = serializers.FloatField(help_text="Radio de búsqueda en kilómetros")
    count = serializers.IntegerField(help_text="Cantidad de albergues encontrados")
    results = HostelSerializer(many=True, help_text="Lista de albergues cercanos")

# ============================================================================
# SERIALIZERS PARA RESERVAS DE ALBERGUES
# ============================================================================

class HostelReservationSerializer(serializers.ModelSerializer):
    """Serializer para reservas de albergues"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    hostel_name = serializers.CharField(source='hostel.name', read_only=True)
    hostel_location = serializers.CharField(source='hostel.get_formatted_address', read_only=True)
    total_people = serializers.SerializerMethodField(help_text="Total de personas en la reserva")
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    # Hacer el campo status opcional para creación
    status = serializers.ChoiceField(
        choices=HostelReservation.ReservationStatus.choices,
        required=False,
        help_text="Estado de la reserva (por defecto: pending)"
    )
    
    class Meta:
        model = HostelReservation
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'hostel', 'hostel_name', 'hostel_location',
            'status', 'status_display', 'type', 'type_display', 'arrival_date',
            'men_quantity', 'women_quantity', 'total_people',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'user_phone', 'hostel_name', 'hostel_location',
            'status_display', 'type_display', 'total_people',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_total_people(self, obj) -> int:
        men = obj.men_quantity or 0
        women = obj.women_quantity or 0
        return men + women
    
    def get_created_by_name(self, obj) -> str:
        """Obtener el nombre de quien creó la reserva"""
        return obj.get_created_by_name()
    
    def validate(self, attrs):
        men_quantity = attrs.get('men_quantity')
        women_quantity = attrs.get('women_quantity')
        
        if not men_quantity and not women_quantity:
            raise serializers.ValidationError(
                "Debe especificar al menos una cantidad (hombres o mujeres)"
            )
        
        if self.instance is None:
            hostel = attrs.get('hostel')
            if hostel:
                self._validate_capacity_availability(hostel, men_quantity or 0, women_quantity or 0)
        
        return attrs
    
    def _validate_capacity_availability(self, hostel, men_quantity, women_quantity):
        if not hostel.has_capacity_for(men_quantity, women_quantity):
            available = hostel.get_available_capacity()
            raise serializers.ValidationError(
                f"No hay suficiente capacidad disponible. "
                f"Disponible - Hombres: {available['men']}, Mujeres: {available['women']}. "
                f"Solicitado - Hombres: {men_quantity}, Mujeres: {women_quantity}"
            )
    
    def validate_arrival_date(self, value):
        from django.utils import timezone
        from datetime import date
        
        if value < date.today():
            raise serializers.ValidationError(
                "La fecha de llegada no puede ser en el pasado"
            )
        
        return value

class HostelReservationUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar solo el status de reservas"""
    
    class Meta:
        model = HostelReservation
        fields = ['status']
    
    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'is_staff') and request.user.is_staff:
                # Es un AdminUser
                instance.updated_by_admin = request.user
            else:
                # Es un CustomUser
                instance.updated_by_user = request.user
        
        instance.status = new_status
        instance.save()  # La actualización de capacidad se maneja automáticamente en el modelo
        
        return instance

class BulkStatusUpdateSerializer(serializers.Serializer):
    """Serializer para actualización masiva de estados de reservas"""
    reservation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Lista de IDs de reservas a actualizar"
    )
    status = serializers.ChoiceField(
        choices=HostelReservation.ReservationStatus.choices,
        help_text="Nuevo estado para las reservas"
    )
    
    def validate_reservation_ids(self, value):
        if not value:
            raise serializers.ValidationError("La lista de IDs no puede estar vacía")
        return value
