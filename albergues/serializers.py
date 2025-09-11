# serializers.py
from rest_framework import serializers
from typing import Dict, Any, Tuple
from .models import Location, Hostel, HostelReservation

# ============================================================================
# SERIALIZERS PARA UBICACIONES
# ============================================================================

class LocationSerializer(serializers.ModelSerializer):
    """Serializer para ubicaciones geográficas"""
    coordinates = serializers.SerializerMethodField()
    google_maps_url = serializers.SerializerMethodField()
    formatted_address = serializers.SerializerMethodField()
    
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
        """Retorna las coordenadas como tupla"""
        return obj.get_coordinates()
    
    def get_google_maps_url(self, obj) -> str:
        """Retorna URL de Google Maps"""
        return obj.get_google_maps_url()
    
    def get_formatted_address(self, obj) -> str:
        """Retorna dirección formateada"""
        return obj.get_formatted_address()

# ============================================================================
# SERIALIZERS PARA ALBERGUES
# ============================================================================

class HostelSerializer(serializers.ModelSerializer):
    """Serializer para albergues"""
    location_data = LocationSerializer(source='location', read_only=True)
    total_capacity = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    formatted_address = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Hostel
        fields = [
            'id', 'name', 'phone', 'men_capacity', 'women_capacity', 'is_active',
            'location', 'location_data', 'total_capacity', 'coordinates', 'formatted_address',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'location_data', 'total_capacity', 'coordinates', 'formatted_address',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_total_capacity(self, obj) -> int:
        """Retorna la capacidad total del albergue"""
        men_cap = obj.men_capacity or 0
        women_cap = obj.women_capacity or 0
        return men_cap + women_cap
    
    def get_coordinates(self, obj) -> Tuple[float, float]:
        """Retorna las coordenadas del albergue"""
        return obj.get_coordinates()
    
    def get_formatted_address(self, obj) -> str:
        """Retorna dirección formateada del albergue"""
        return obj.get_formatted_address()
    
    def validate(self, attrs):
        """Validar que al menos una capacidad sea especificada"""
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
            'name', 'phone', 'men_capacity', 'women_capacity', 'is_active', 'location'
        ]
    
    def create(self, validated_data):
        location_data = validated_data.pop('location')
        location = Location.objects.create(**location_data)
        hostel = Hostel.objects.create(location=location, **validated_data)
        return hostel
    
    def validate(self, attrs):
        """Validar que al menos una capacidad sea especificada"""
        men_capacity = attrs.get('men_capacity')
        women_capacity = attrs.get('women_capacity')
        
        if not men_capacity and not women_capacity:
            raise serializers.ValidationError(
                "Debe especificar al menos una capacidad (hombres o mujeres)"
            )
        
        return attrs

# ============================================================================
# SERIALIZERS PARA RESERVAS DE ALBERGUES
# ============================================================================

class HostelReservationSerializer(serializers.ModelSerializer):
    """Serializer para reservas de albergues"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    hostel_name = serializers.CharField(source='hostel.name', read_only=True)
    hostel_location = serializers.CharField(source='hostel.get_formatted_address', read_only=True)
    total_people = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
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
        """Retorna el total de personas en la reserva"""
        men = obj.men_quantity or 0
        women = obj.women_quantity or 0
        return men + women
    
    def validate(self, attrs):
        """Validar que al menos una cantidad sea especificada"""
        men_quantity = attrs.get('men_quantity')
        women_quantity = attrs.get('women_quantity')
        
        if not men_quantity and not women_quantity:
            raise serializers.ValidationError(
                "Debe especificar al menos una cantidad (hombres o mujeres)"
            )
        
        return attrs
    
    def validate_arrival_date(self, value):
        """Validar que la fecha de llegada no sea en el pasado"""
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
        """Actualizar solo el status y registrar quién lo modificó"""
        instance.status = validated_data.get('status', instance.status)
        
        # Registrar quién modificó la reserva si hay usuario en contexto
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            instance.updated_by = request.user
        
        instance.save()
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
        """Validar que la lista no esté vacía"""
        if not value:
            raise serializers.ValidationError("La lista de IDs no puede estar vacía")
        return value
