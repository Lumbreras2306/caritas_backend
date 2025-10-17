# models.py
import uuid
import re
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


# ============================================================================
# VALIDADORES Y CHOICES
# ============================================================================

# Patrón regex para números de teléfono internacionales (requiere +código)
PHONE_REGEX_PATTERN = r'^\+\d{10,15}$'

phone_regex = RegexValidator(
    regex=PHONE_REGEX_PATTERN,
    message="El número de teléfono debe estar en formato internacional con código de país: '+521234567890'. Ejemplo: +52811908593"
)

def validate_phone_number(value):
    """
    Función de validación personalizada para números de teléfono.
    REQUIERE formato internacional con código de país: +52XXXXXXXXXX
    """
    if not value:
        return False
    
    # Limpiar espacios y caracteres especiales excepto el +
    cleaned = re.sub(r'[^\d+]', '', value)
    
    # DEBE empezar con + (formato internacional obligatorio)
    if not cleaned.startswith('+'):
        return False
    
    # Verificar que solo contenga + seguido de dígitos
    if not re.match(r'^\+\d+$', cleaned):
        return False
    
    # Verificar longitud (mínimo 11, máximo 16 dígitos incluyendo el +)
    if len(cleaned) < 11 or len(cleaned) > 16:
        return False
    
    # Verificar que el código de país tenga al menos 1 dígito y el número tenga al menos 10
    digits_only = cleaned[1:]  # Quitar el +
    if len(digits_only) < 11:  # Código de país (1-3) + número (10)
        return False
    
    return True

class STATUS_CHOICES(models.TextChoices):
    PENDING = 'PENDING', 'Pendiente'
    APPROVED = 'APPROVED', 'Aprobado'
    REJECTED = 'REJECTED', 'Rechazado'

class GENDER_CHOICES(models.TextChoices):
    M = 'M', 'Masculino'
    F = 'F', 'Femenino'

class POVERTY_LEVEL_CHOICES(models.TextChoices):
    LEVEL_1 = 'LEVEL_1', 'Nivel 1'
    LEVEL_2 = 'LEVEL_2', 'Nivel 2'
    LEVEL_3 = 'LEVEL_3', 'Nivel 3'

# ============================================================================
# MODELOS BASE DE AUDITORÍA
# ============================================================================

class AuditModel(models.Model):
    """Modelo base para auditoría - Solo para AdminUser"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")
    created_by = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        verbose_name="Actualizado por"
    )

    class Meta:
        abstract = True

class FlexibleAuditModel(models.Model):
    """Modelo base para auditoría flexible - Permite tanto AdminUser como CustomUser"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")
    
    # Campos de auditoría flexibles que pueden ser AdminUser o CustomUser
    created_by_admin = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by_admin",
        verbose_name="Creado por (Admin)"
    )
    created_by_user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by_user",
        verbose_name="Creado por (Usuario)"
    )
    updated_by_admin = models.ForeignKey(
        'users.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated_by_admin",
        verbose_name="Actualizado por (Admin)"
    )
    updated_by_user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated_by_user",
        verbose_name="Actualizado por (Usuario)"
    )

    class Meta:
        abstract = True
    
    def get_created_by_name(self):
        """Retorna el nombre de quien creó el registro"""
        if self.created_by_admin:
            return self.created_by_admin.get_full_name()
        elif self.created_by_user:
            return self.created_by_user.get_full_name()
        return "Sistema"
    
    def get_updated_by_name(self):
        """Retorna el nombre de quien actualizó el registro"""
        if self.updated_by_admin:
            return self.updated_by_admin.get_full_name()
        elif self.updated_by_user:
            return self.updated_by_user.get_full_name()
        return "Sistema"

# ============================================================================
# MANAGERS PERSONALIZADOS
# ============================================================================

class AdminUserManager(BaseUserManager):
    """Manager personalizado para el modelo AdminUser"""
    
    def create_user(self, username, password=None, **extra_fields):
        """Crear y guardar un usuario administrador"""
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, **extra_fields):
        """Crear y guardar un superusuario administrador"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, password, **extra_fields)

# ============================================================================
# MODELOS DE ADMINISTRADORES
# ============================================================================

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
    
    # Información personal
    first_name = models.CharField(max_length=150, verbose_name="Nombre")
    last_name = models.CharField(max_length=150, verbose_name="Apellido")
    
    # Campos de albergue (relación opcional para filtrado)
    main_hostel = models.ForeignKey(
        'albergues.Hostel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Albergue principal"
    )
    
    # Campos de estado
    is_active = models.BooleanField(default=True, verbose_name="Usuario activo")
    is_staff = models.BooleanField(default=True, verbose_name="Es staff")
    is_superuser = models.BooleanField(default=False, verbose_name="Es superusuario")
    
    # Campos de auditoría
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Creado en")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Actualizado en")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Último acceso")
    
    objects = AdminUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
        ordering = ['-last_login', '-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """Retorna el nombre completo del administrador"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retorna el nombre corto del administrador"""
        return self.first_name

# ============================================================================
# MODELOS DE PRE-REGISTRO
# ============================================================================

class PreRegisterUser(AuditModel):
    """
    Modelo para usuarios que solicitan pre-registro.
    Requieren aprobación de administrador antes de convertirse en CustomUser.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información básica
    first_name = models.CharField(max_length=150, verbose_name="Nombre")
    last_name = models.CharField(max_length=150, verbose_name="Apellido")
    phone_number = models.CharField(
        max_length=17,
        unique=True,
        validators=[phone_regex],
        verbose_name="Número de teléfono"
    )
    age = models.PositiveIntegerField(verbose_name="Edad")
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES.choices,
        verbose_name="Género"
    )
    
    # Estado y consentimiento
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES.choices,
        default=STATUS_CHOICES.PENDING,
        verbose_name="Estado"
    )
    privacy_policy_accepted = models.BooleanField(
        default=False,
        verbose_name="Política de privacidad aceptada"
    )
    
    class Meta:
        verbose_name = "Pre-registro de Usuario"
        verbose_name_plural = "Pre-registros de Usuarios"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number}) - {self.get_status_display()}"
    
    def get_full_name(self):
        """Retorna el nombre completo del pre-usuario"""
        return f"{self.first_name} {self.last_name}".strip()

# ============================================================================
# MODELOS DE USUARIOS FINALES
# ============================================================================

class CustomUser(AuditModel):
    """
    Modelo para usuarios finales del sistema.
    Son creados por administradores después de aprobar pre-registros.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Información básica
    first_name = models.CharField(max_length=150, verbose_name="Nombre")
    last_name = models.CharField(max_length=150, verbose_name="Apellido")
    phone_number = models.CharField(
        max_length=17,
        unique=True,
        validators=[phone_regex],
        verbose_name="Número de teléfono"
    )
    age = models.PositiveIntegerField(verbose_name="Edad")
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES.choices,
        verbose_name="Género"
    )
    
    # Información adicional
    poverty_level = models.CharField(
        max_length=20,
        choices=POVERTY_LEVEL_CHOICES.choices,
        default=POVERTY_LEVEL_CHOICES.LEVEL_1,
        verbose_name="Nivel de pobreza"
    )
    
    # Estado del usuario
    is_active = models.BooleanField(
        default=True,
        verbose_name="Usuario activo"
    )
    
    # Campos de auditoría
    approved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Aprobado en"
    )
    approved_by = models.ForeignKey(
        AdminUser,
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
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_active']),
        ]
    
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
    
    @property
    def is_authenticated(self):
        """
        Propiedad para compatibilidad con Django's authentication system.
        Siempre retorna True para usuarios CustomUser activos.
        """
        return self.is_active
    
    @property
    def is_anonymous(self):
        """
        Propiedad para compatibilidad con Django's authentication system.
        Siempre retorna False para usuarios CustomUser.
        """
        return False

# ============================================================================
# MODELO DE TOKEN PARA CUSTOMUSER (COMPATIBLE CON DRF)
# ============================================================================

class CustomUserToken(models.Model):
    """
    Token para usuarios finales (CustomUser) compatible con DRF.
    Usa el mismo patrón que rest_framework.authtoken.models.Token.
    """
    key = models.CharField(max_length=40, primary_key=True, verbose_name="Clave del token")
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='auth_token',
        verbose_name="Usuario"
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    
    class Meta:
        verbose_name = "Token de Usuario"
        verbose_name_plural = "Tokens de Usuarios"
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)
    
    def generate_key(self):
        """Genera una clave de token única de 40 caracteres"""
        import secrets
        import hashlib
        # Generar un token de 40 caracteres exactos
        raw_token = secrets.token_urlsafe(32)
        return hashlib.sha256(raw_token.encode()).hexdigest()[:40]
    
    def __str__(self):
        return f"Token para {self.user.get_full_name()}"

class PrivacyPolicy(models.Model):
    """
    Modelo para la política de privacidad.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.FileField(upload_to='privacy_policies/', verbose_name="Política de privacidad")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")
    
    class Meta:
        verbose_name = "Política de Privacidad"
        verbose_name_plural = "Políticas de Privacidad"
    
    def __str__(self):
        return f"Política de privacidad {self.id}"
