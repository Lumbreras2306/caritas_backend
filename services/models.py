from django.db import models
from users.models import AuditModel, FlexibleAuditModel
from albergues.models import Hostel

import uuid
from datetime import timedelta

########################################################
# MODELOS DE SERVICIOS
########################################################

class Service(AuditModel):
    """
    Modelo para servicios.
    """
    class ReservationType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        GROUP = "group", "Grupo"

    # Campos principales
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripción")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    reservation_type = models.CharField(max_length=255, verbose_name="Tipo de reserva", choices=ReservationType.choices)
    needs_approval = models.BooleanField(default=False, verbose_name="Necesita aprobación")
    max_time = models.PositiveIntegerField(verbose_name="Tiempo máximo de reserva", help_text="Tiempo máximo de reserva en minutos")

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['-created_at']

class ServiceSchedule(AuditModel):
    """
    Modelo para horarios de servicios.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    day_of_week = models.IntegerField(verbose_name="Día de la semana")
    start_time = models.TimeField(verbose_name="Hora de inicio")
    end_time = models.TimeField(verbose_name="Hora de fin")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")

    class Meta:
        verbose_name = "Horario de servicio"
        verbose_name_plural = "Horarios de servicio"
        ordering = ['-created_at']

class HostelService(AuditModel):
    """
    Modelo para servicios de albergues.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hostel = models.ForeignKey('albergues.Hostel', on_delete=models.CASCADE, verbose_name="Albergue")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Servicio")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    # Opcionales
    schedule = models.ForeignKey(ServiceSchedule, on_delete=models.CASCADE, verbose_name="Horario", null=True, blank=True)

    class Meta:
        verbose_name = "Servicio de albergue"
        verbose_name_plural = "Servicios de albergue"
        ordering = ['-created_at']

class ReservationService(FlexibleAuditModel):
    """
    Modelo para reservas de servicios.
    """
    class ReservationStatus(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmada"
        CANCELLED = "cancelled", "Cancelada"
        REJECTED = "rejected", "Rechazada"
        COMPLETED = "completed", "Completada"
        IN_PROGRESS = "in_progress", "En progreso"

    class ReservationType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        GROUP = "group", "Grupo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, verbose_name="Usuario")
    service = models.ForeignKey(HostelService, on_delete=models.CASCADE, verbose_name="Servicio")
    status = models.CharField(max_length=255, verbose_name="Estado", choices=ReservationStatus.choices)
    type = models.CharField(max_length=255, verbose_name="Tipo", choices=ReservationType.choices)

    # Campos específicos
    men_quantity = models.PositiveIntegerField(verbose_name="Cantidad de hombres", null=True, blank=True)
    women_quantity = models.PositiveIntegerField(verbose_name="Cantidad de mujeres", null=True, blank=True)

    datetime_reserved = models.DateTimeField(verbose_name="Fecha y hora de reserva")
    end_datetime_reserved = models.DateTimeField(verbose_name="Fecha y hora de fin de reserva")

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(men_quantity__isnull=False) | models.Q(women_quantity__isnull=False),
                name='service_reservation_at_least_one_quantity_required'
            )
        ]

    def calculate_end_time(self):
        return self.datetime_reserved + timedelta(minutes=self.service.service.max_time)

    def save(self, *args, **kwargs):
        self.end_datetime_reserved = self.calculate_end_time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.service.name} - {self.status}"
