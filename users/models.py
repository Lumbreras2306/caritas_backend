from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.db.models import Q, Index
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from albergues.models import Hostel
else:
    Hostel = 'albergues.Hostel'

########################################################
# CONSTANTES Y VALIDADORES
########################################################

GENDER_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Femenino')
]

class STATUS_CHOICES(models.TextChoices):
    PENDING = "pending", "Pendiente"
    APPROVED = "approved", "Aprobado"
    REJECTED = "rejected", "Rechazado"

phone_regex = RegexValidator(
    regex=r'^\+\d{1,3}\s\d{7,15}$',
    message="El número telefónico debe estar en formato: '+XX XXXXXXXXXX'."
)

########################################################
# MODELOS DE AUDITORIA
########################################################

class AuditModel(models.Model):
    """
    Modelo base para auditoría.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deactivated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Desactivado en"
    )
    created_by = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Creado por",
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Actualizado por",
        related_name='%(class)s_updated'
    )
    deactivated_by = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Desactivado por",
        related_name='%(class)s_deactivated'
    )

    class Meta:
        abstract = True

########################################################
# MODELOS DE USUARIOS
########################################################

class PreRegisterUser(AuditModel):
    """
    Modelo para usuarios que se registran pero no han sido aprobados.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        unique=True,
        verbose_name="Número telefónico",
        db_index=True
    )
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    privacy_policy_accepted = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES.choices, default=STATUS_CHOICES.PENDING)

    class Meta:
        verbose_name = "Usuario pre-registro"
        verbose_name_plural = "Usuarios pre-registro"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario"""
        return self.first_name

class CustomUser(AuditModel):
    """
    Modelo de usuario personalizado para usuarios finales.
    Utiliza número telefónico en lugar de username/email.
    """
    # Campos principales
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        unique=True,
        verbose_name="Número telefónico",
        db_index=True
    )
    
    # Información personal
    first_name = models.CharField(max_length=150, verbose_name="Nombre")
    last_name = models.CharField(max_length=150, verbose_name="Apellido")
    age = models.PositiveIntegerField(verbose_name="Edad")
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES, 
        verbose_name="Género"
    )
    
    # Información socioeconómica
    poverty_level = models.PositiveIntegerField(
        validators=[MinValueValidator(5), MaxValueValidator(10)],
        verbose_name="Nivel de pobreza (5-10)",
        help_text="Pobreza extrema <= 6.5, Pobreza moderada <= 8.5, Fuera de riesgo <= 10"
    )
    
    # Campos de estado
    is_active = models.BooleanField(
        default=True,
        verbose_name="Cuenta activa"
    )

    # Campos de auditoría
    approved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Aprobado en"
    )
    approved_by = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Aprobado por",
        related_name='custom_users_approved'
    )
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario"""
        return self.first_name
    
    def approve_user(self, admin_user):
        """Aprueba al usuario y registra quién lo aprobó"""
        self.is_active = True
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.save()

########################################################
# MODELOS DE ADMINISTRADORES
########################################################

class AdminUserManager(BaseUserManager):
    """Manager personalizado para el modelo AdminUser"""
    
    def create_user(self, username, password, **extra_fields):
        """Crear y guardar un usuario administrador"""
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password, **extra_fields):
        """Crear y guardar un superusuario administrador"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, password, **extra_fields)


class AdminUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo para usuarios administradores del backend.
    Tienen acceso completo al sistema de administración.
    """
    
    # Campos principales
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        max_length=150, 
        unique=True,
        verbose_name="Nombre de usuario"
    )
    
    # Campos de albergue
    """ ESTA RELACIÓN ES ÚNICAMENTE PARA FILTRADO RÁPIDO, NO PARA RESTRICCIÓN DE ACCESO """
    main_hostel = models.OneToOneField(
        'albergues.Hostel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Albergue principal"
    )
    
    # Información personal
    first_name = models.CharField(max_length=150, verbose_name="Nombre")
    last_name = models.CharField(max_length=150, verbose_name="Apellido")
    
    # Campos de estado
    is_active = models.BooleanField(
        default=True,
        verbose_name="Usuario activo"
    )
    is_staff = models.BooleanField(
        default=True,
        verbose_name="Es staff"
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="Es superusuario"
    )
    
    # Campos de auditoría
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Último acceso")
    
    objects = AdminUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
        ordering = ['-last_login']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """Retorna el nombre completo del administrador"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retorna el nombre corto del administrador"""
        return self.first_name

    def get_last_login(self):
        """Retorna el último acceso del administrador"""
        return self.last_login

########################################################
# MODELOS DE CÓDIGOS DE VERIFICACIÓN OTP
########################################################

class OTPCode(AuditModel):
    """
    Modelo para almacenar códigos de verificación OTP hasheados.
    """
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        SIGNUP = "signup", "Signup"
        PASSWORD_RESET = "password_reset", "Password reset"
        PHONE_CHANGE = "phone_change", "Phone change"

    class Channel(models.TextChoices):
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "Whatsapp"
        EMAIL = "email", "Email"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name="otps")
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    hashed_code = models.CharField(max_length=255)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    meta_ip = models.GenericIPAddressField(null=True, blank=True)
    meta_ua = models.TextField(blank=True)

    class Meta:
        verbose_name = "Código de verificación OTP"
        verbose_name_plural = "Códigos de verificación OTP"
        ordering = ['-created_at']
        constraints = [
            # Al menos uno activo por user+purpose
            models.UniqueConstraint(
                fields=['user', 'purpose'],
                condition=Q(consumed_at__isnull=True),
                name='uniq_active_otp_per_user_purpose',
            ),
            models.CheckConstraint(check=Q(max_attempts__gte=1), name='otp_max_attempts_gte_1'),
        ]
        indexes = [
            Index(fields=['user', 'purpose']),
            Index(fields=['user', 'purpose', 'expires_at']),
        ]

    def __str__(self):
        return f"OTP {self.purpose} → {self.user.get_full_name()} ({self.user.phone_number}) exp={self.expires_at.isoformat()}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return (self.consumed_at is None) and (not self.is_expired()) and (self.attempts < self.max_attempts)
