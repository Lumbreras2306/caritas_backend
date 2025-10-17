from django.db import models
from users.models import AuditModel, FlexibleAuditModel, phone_regex
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
        db_index=True
    )
    location = models.OneToOneField(
        Location, 
        on_delete=models.CASCADE,
        verbose_name="Ubicación",
        related_name="hostel"
    )
    men_capacity = models.PositiveIntegerField(
        verbose_name="Capacidad de hombres",
        help_text="Número máximo de hombres que puede albergar el albergue",
        null=True,
        blank=True
    )
    current_men_capacity = models.PositiveIntegerField(
        verbose_name="Capacidad de hombres actual",
        help_text="Número de hombres que actualmente alberga el albergue",
        null=True,
        blank=True
    )
    women_capacity = models.PositiveIntegerField(
        verbose_name="Capacidad de mujeres",
        help_text="Número máximo de mujeres que puede albergar el albergue",
        null=True,
        blank=True
    )
    current_women_capacity = models.PositiveIntegerField(
        verbose_name="Capacidad de mujeres actual",
        help_text="Número de mujeres que actualmente alberga el albergue",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el albergue está activo"
    )
    image_url = models.URLField(
        verbose_name="URL de la imagen del albergue",
        help_text="URL de la imagen del albergue",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Albergue"
        verbose_name_plural = "Albergues"
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(men_capacity__isnull=False) | models.Q(women_capacity__isnull=False),
                name='at_least_one_capacity_required'
            )
        ]

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
        men_cap = self.men_capacity or 0
        women_cap = self.women_capacity or 0
        return men_cap + women_cap
    
    def get_current_capacity(self):
        """Retorna la capacidad actual del albergue"""
        men_current = self.current_men_capacity or 0
        women_current = self.current_women_capacity or 0
        return men_current + women_current
    
    def get_available_capacity(self):
        """Retorna la capacidad disponible del albergue"""
        men_total = self.men_capacity or 0
        women_total = self.women_capacity or 0
        men_current = self.current_men_capacity or 0
        women_current = self.current_women_capacity or 0
        
        return {
            'men': max(0, men_total - men_current),
            'women': max(0, women_total - women_current),
            'total': max(0, (men_total + women_total) - (men_current + women_current))
        }
    
    def has_capacity_for(self, men_quantity=0, women_quantity=0):
        """Verifica si el albergue tiene capacidad para la cantidad especificada"""
        available = self.get_available_capacity()
        return men_quantity <= available['men'] and women_quantity <= available['women']
    
    def add_to_current_capacity(self, men_quantity=0, women_quantity=0):
        """Agrega cantidad a la capacidad actual del albergue"""
        if men_quantity > 0:
            current_men = self.current_men_capacity or 0
            self.current_men_capacity = current_men + men_quantity
        
        if women_quantity > 0:
            current_women = self.current_women_capacity or 0
            self.current_women_capacity = current_women + women_quantity
        
        self.save(update_fields=['current_men_capacity', 'current_women_capacity'])
    
    def remove_from_current_capacity(self, men_quantity=0, women_quantity=0):
        """Quita cantidad de la capacidad actual del albergue"""
        if men_quantity > 0:
            current_men = self.current_men_capacity or 0
            self.current_men_capacity = max(0, current_men - men_quantity)
        
        if women_quantity > 0:
            current_women = self.current_women_capacity or 0
            self.current_women_capacity = max(0, current_women - women_quantity)
        
        self.save(update_fields=['current_men_capacity', 'current_women_capacity'])

class HostelReservation(FlexibleAuditModel):
    """
    Modelo para reservas de albergues.
    """
    class ReservationStatus(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmada"
        CANCELLED = "cancelled", "Cancelada"
        REJECTED = "rejected", "Rechazada"
        CHECKED_IN = "checked_in", "Check-in"
        CHECKED_OUT = "checked_out", "Check-out"

    class ReservationType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        GROUP = "group", "Grupo"

    # Campos principales
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, verbose_name="Usuario")
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, verbose_name="Albergue")
    status = models.CharField(
        default=ReservationStatus.PENDING, 
        max_length=255, 
        verbose_name="Estado", 
        choices=ReservationStatus.choices,
        blank=True,
        null=True
    )
    type = models.CharField(max_length=255, verbose_name="Tipo", choices=ReservationType.choices)

    # Campos específicos
    arrival_date = models.DateField(verbose_name="Fecha de llegada")
    men_quantity = models.PositiveIntegerField(verbose_name="Cantidad de hombres", null=True, blank=True)
    women_quantity = models.PositiveIntegerField(verbose_name="Cantidad de mujeres", null=True, blank=True)

    class Meta:
        verbose_name = "Reserva de albergue"
        verbose_name_plural = "Reservas de albergue"
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(men_quantity__isnull=False) | models.Q(women_quantity__isnull=False),
                name='hostel_reservation_at_least_one_quantity_required'
            )
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.hostel.name} - {self.status}"

    def save(self, *args, **kwargs):
        """Override save para actualizar automáticamente la capacidad del albergue"""
        # Obtener el estado anterior si existe
        old_status = None
        if self.pk:
            try:
                old_instance = HostelReservation.objects.get(pk=self.pk)
                old_status = old_instance.status
            except HostelReservation.DoesNotExist:
                pass
        
        # Asegurar que el status tenga un valor por defecto si es None
        if self.status is None:
            self.status = self.ReservationStatus.PENDING
        
        # Guardar la instancia
        super().save(*args, **kwargs)
        
        # Actualizar capacidad del albergue si el estado cambió
        if old_status != self.status:
            self._update_hostel_capacity(old_status, self.status)
    
    def _update_hostel_capacity(self, old_status, new_status):
        """Actualiza la capacidad del albergue basado en el cambio de estado"""
        hostel = self.hostel
        men_quantity = self.men_quantity or 0
        women_quantity = self.women_quantity or 0
        
        # Si se hace check-in (entrada al albergue) - ACTUALIZA la capacidad
        if new_status == self.ReservationStatus.CHECKED_IN:
            # Verificar que hay capacidad disponible
            if not hostel.has_capacity_for(men_quantity, women_quantity):
                raise ValueError(
                    f"No hay capacidad suficiente en el albergue. "
                    f"Disponible: {hostel.get_available_capacity()}, "
                    f"Solicitado: {men_quantity} hombres, {women_quantity} mujeres"
                )
            # Agregar a la capacidad actual
            hostel.add_to_current_capacity(men_quantity, women_quantity)
        
        # Si se hace check-out (salida del albergue) - LIBERA la capacidad
        elif new_status == self.ReservationStatus.CHECKED_OUT:
            # Liberar la capacidad
            hostel.remove_from_current_capacity(men_quantity, women_quantity)
        
        # Si se cancela o rechaza una reserva que ya estaba ocupando espacio
        elif (old_status == self.ReservationStatus.CHECKED_IN and 
              new_status in [self.ReservationStatus.CANCELLED, self.ReservationStatus.REJECTED]):
            # Liberar la capacidad que estaba ocupando
            hostel.remove_from_current_capacity(men_quantity, women_quantity)
        
        # Si se confirma una reserva pendiente - SOLO VERIFICA, NO actualiza
        elif (old_status == self.ReservationStatus.PENDING and 
              new_status == self.ReservationStatus.CONFIRMED):
            # Solo verificar capacidad disponible, NO actualizar
            if not hostel.has_capacity_for(men_quantity, women_quantity):
                raise ValueError(
                    f"No hay capacidad suficiente en el albergue. "
                    f"Disponible: {hostel.get_available_capacity()}, "
                    f"Solicitado: {men_quantity} hombres, {women_quantity} mujeres"
                )
            # NO se actualiza la capacidad aquí, solo se verifica
