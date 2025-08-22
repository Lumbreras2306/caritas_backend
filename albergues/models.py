from django.db import models
from users.models import AuditModel, phone_regex
import uuid

########################################################
# MODELOS DE ALBERGUES
########################################################

class Location(AuditModel):
    """
    Modelo para almacenar información de ubicación geográfica.
    Permite reutilización para otros tipos de entidades.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        verbose_name="Latitud",
        help_text="Coordenada de latitud (ej: 19.4326)"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        verbose_name="Longitud",
        help_text="Coordenada de longitud (ej: -99.1332)"
    )
    address = models.CharField(max_length=255, verbose_name="Dirección")
    city = models.CharField(max_length=255, verbose_name="Ciudad")
    state = models.CharField(max_length=255, verbose_name="Estado")
    country = models.CharField(
        max_length=100, 
        verbose_name="País",
        default="México"
    )
    zip_code = models.CharField(max_length=20, verbose_name="Código postal")
    timezone = models.CharField(
        max_length=50, 
        verbose_name="Zona horaria",
        default="America/Mexico_City"
    )
    landmarks = models.TextField(
        blank=True, 
        verbose_name="Puntos de referencia",
        help_text="Descripción de puntos de referencia cercanos"
    )
    
    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['city', 'state']),
        ]

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state}"

    def get_coordinates(self):
        """Retorna las coordenadas como tupla (lat, lng)"""
        return (float(self.latitude), float(self.longitude))

    def get_google_maps_url(self):
        """Genera URL directa a Google Maps"""
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"

    def get_formatted_address(self):
        """Retorna dirección completa formateada"""
        parts = [self.address, self.city, self.state, self.zip_code, self.country]
        return ", ".join(filter(None, parts))


class Hostel(AuditModel):
    """
    Modelo para albergues.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nombre")
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        unique=True,
        verbose_name="Número telefónico",
        index=True
    )
    location = models.OneToOneField(
        Location, 
        on_delete=models.CASCADE,
        verbose_name="Ubicación",
        related_name="hostel"
    )
    men_capacity = models.PositiveIntegerField(
        verbose_name="Capacidad de hombres",
        help_text="Número máximo de hombres que puede albergar el albergue"
    )
    women_capacity = models.PositiveIntegerField(
        verbose_name="Capacidad de mujeres",
        help_text="Número máximo de mujeres que puede albergar el albergue"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el albergue está activo"
    )

    class Meta:
        verbose_name = "Albergue"
        verbose_name_plural = "Albergues"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.location.city}, {self.location.state}"

    def get_coordinates(self):
        """Retorna las coordenadas del albergue"""
        return self.location.get_coordinates()

    def get_google_maps_url(self):
        """Retorna URL directa a Google Maps"""
        return self.location.get_google_maps_url()

    def get_formatted_address(self):
        """Retorna dirección completa formateada"""
        return self.location.get_formatted_address()

    def get_total_capacity(self):
        """Retorna la capacidad total del albergue"""
        return self.men_capacity + self.women_capacity