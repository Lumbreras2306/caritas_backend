# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import (
    CustomUser, PreRegisterUser, AdminUser, PrivacyPolicy,
    STATUS_CHOICES, phone_regex, validate_phone_number
)

# ============================================================================
# SERIALIZERS DE RESPUESTAS ESTÁNDAR
# ============================================================================

class ErrorResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de error estándar"""
    error = serializers.CharField(help_text="Mensaje de error")
    detail = serializers.CharField(required=False, help_text="Detalle adicional del error")
    field_errors = serializers.DictField(required=False, help_text="Errores específicos por campo")

class SuccessResponseSerializer(serializers.Serializer):
    """Serializer para respuestas exitosas estándar"""
    message = serializers.CharField(help_text="Mensaje de éxito")
    data = serializers.DictField(required=False, help_text="Datos adicionales")

class TokenResponseSerializer(serializers.Serializer):
    """Serializer para respuestas con token"""
    token = serializers.CharField(help_text="Token de autenticación")
    user_id = serializers.UUIDField(help_text="ID del usuario")
    username = serializers.CharField(required=False, help_text="Nombre de usuario (solo admins)")
    full_name = serializers.CharField(help_text="Nombre completo del usuario")
    is_superuser = serializers.BooleanField(required=False, help_text="Es superusuario (solo admins)")

# ============================================================================
# SERIALIZERS PARA USUARIOS PRE-REGISTRO
# ============================================================================

class PreRegisterUserSerializer(serializers.ModelSerializer):
    """Serializer unificado para PreRegisterUser"""
    
    class Meta:
        model = PreRegisterUser
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 
            'age', 'gender', 'privacy_policy_accepted', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_phone_number(self, value):
        """Validar número de teléfono"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("El número de teléfono debe estar en formato internacional con código de país. Ejemplo: +52811908593")
        return value
    
    def validate_age(self, value):
        """Validar edad"""
        if value < 18:
            raise serializers.ValidationError("Debe ser mayor de 18 años")
        if value > 100:
            raise serializers.ValidationError("Edad no válida")
        return value
    
    def validate_status(self, value):
        """Validar status"""
        valid_statuses = [choice[0] for choice in STATUS_CHOICES.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status debe ser uno de: {', '.join(valid_statuses)}")
        return value
    
    def create(self, validated_data):
        user_exists = CustomUser.objects.filter(phone_number=validated_data['phone_number']).exists()
        if user_exists:
            raise serializers.ValidationError("El usuario ya existe, por favor contacte al administrador")
        
        pre_register = PreRegisterUser.objects.filter(phone_number=validated_data['phone_number']).first()
        if pre_register:
            if pre_register.status == STATUS_CHOICES.PENDING:
                raise serializers.ValidationError("El pre-registro está pendiente de aprobación")
            elif pre_register.status == STATUS_CHOICES.APPROVED:
                raise serializers.ValidationError("El pre-registro ya fue aprobado")
            elif pre_register.status == STATUS_CHOICES.REJECTED:
                raise serializers.ValidationError("El pre-registro fue rechazado. Contacte al administrador.")
        
        return super().create(validated_data)

class PreRegisterVerificationSerializer(serializers.Serializer):
    """Serializer para verificar pre-registro por teléfono"""
    phone_number = serializers.CharField(max_length=17, validators=[phone_regex])
    
    def validate_phone_number(self, value):
        if not validate_phone_number(value):
            raise serializers.ValidationError("El número de teléfono no es válido")
        return value

class PreRegisterVerificationResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de verificación de pre-registro"""
    exists = serializers.BooleanField(help_text="Indica si existe el pre-registro")
    data = PreRegisterUserSerializer(required=False, allow_null=True, help_text="Datos del pre-registro si existe")
    message = serializers.CharField(help_text="Mensaje descriptivo")

# ============================================================================
# SERIALIZERS PARA USUARIOS FINALES
# ============================================================================

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer unificado para CustomUser"""
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 
            'age', 'gender', 'poverty_level', 'is_active',
            'approved_at', 'approved_by_name', 'full_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'approved_at', 'approved_by_name', 'full_name', 'created_at', 'updated_at']
    
    def validate_phone_number(self, value):
        """Validar número de teléfono"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("El número de teléfono debe estar en formato internacional con código de país. Ejemplo: +52811908593")
        return value
    
    def validate_age(self, value):
        """Validar edad"""
        if value < 18:
            raise serializers.ValidationError("Debe ser mayor de 18 años")
        if value > 100:
            raise serializers.ValidationError("Edad no válida")
        return value
    
    def create(self, validated_data):
        user_exists = CustomUser.objects.filter(phone_number=validated_data['phone_number']).exists()
        if user_exists:
            raise serializers.ValidationError("El usuario ya existe")
        
        pre_register = PreRegisterUser.objects.filter(phone_number=validated_data['phone_number']).first()
        if pre_register:
            pre_register.status = STATUS_CHOICES.APPROVED
            pre_register.save()
        
        return super().create(validated_data)

# ============================================================================
# SERIALIZERS PARA ADMINISTRADORES
# ============================================================================

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer unificado para AdminUser"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'full_name', 'is_active', 'is_staff', 
            'is_superuser', 'last_login', 'created_at',
            'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'full_name']
    
    def validate(self, attrs):
        if 'password' in attrs:
            if 'password_confirm' not in attrs:
                raise serializers.ValidationError("Debe confirmar la contraseña")
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        if 'password' in validated_data:
            password = validated_data.pop('password')
            user = AdminUser.objects.create_user(**validated_data)
            user.set_password(password)
            user.save()
            return user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

# ============================================================================
# SERIALIZERS PARA AUTENTICACIÓN
# ============================================================================

class AdminUserLoginSerializer(serializers.Serializer):
    """Serializer para login de administradores"""
    username = serializers.CharField(help_text="Nombre de usuario del administrador")
    password = serializers.CharField(write_only=True, help_text="Contraseña del administrador")
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Credenciales inválidas')
            
            if not user.is_active:
                raise serializers.ValidationError('Usuario desactivado')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Debe incluir usuario y contraseña')

class AdminUserPasswordChangeSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña de administradores"""
    old_password = serializers.CharField(write_only=True, help_text="Contraseña actual")
    new_password = serializers.CharField(write_only=True, min_length=8, help_text="Nueva contraseña (mínimo 8 caracteres)")
    new_password_confirm = serializers.CharField(write_only=True, help_text="Confirmación de nueva contraseña")
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Contraseña actual incorrecta')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('Las contraseñas nuevas no coinciden')
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# ============================================================================
# SERIALIZERS PARA VERIFICACIÓN CON TWILIO
# ============================================================================

class PhoneVerificationSendSerializer(serializers.Serializer):
    """Serializer para enviar código de verificación SMS"""
    phone_number = serializers.CharField(
        max_length=17, 
        validators=[phone_regex],
        help_text="Número de teléfono en formato internacional (ej: +52811908593)"
    )
    
    def validate_phone_number(self, value):
        if not validate_phone_number(value):
            raise serializers.ValidationError("El número de teléfono debe estar en formato internacional con código de país. Ejemplo: +52811908593")
        
        if not CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("No existe un usuario con este número de teléfono")
        
        return value

class PhoneVerificationSendResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de envío de código"""
    message = serializers.CharField(help_text="Mensaje de confirmación")
    phone_number = serializers.CharField(help_text="Número de teléfono al que se envió el código")
    verification_sid = serializers.CharField(help_text="ID de verificación de Twilio")

class PhoneVerificationCheckSerializer(serializers.Serializer):
    """Serializer para verificar código SMS"""
    phone_number = serializers.CharField(
        max_length=17, 
        validators=[phone_regex],
        help_text="Número de teléfono en formato internacional (ej: +52811908593)"
    )
    code = serializers.CharField(
        max_length=6, 
        min_length=6,
        help_text="Código de 6 dígitos enviado por SMS"
    )
    
    def validate_phone_number(self, value):
        if not validate_phone_number(value):
            raise serializers.ValidationError("El número de teléfono debe estar en formato internacional con código de país. Ejemplo: +52811908593")
        return value
    
    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El código debe contener solo números")
        return value

class UserInfoResponseSerializer(serializers.Serializer):
    """Serializer para información del usuario en respuestas"""
    id = serializers.UUIDField(help_text="ID único del usuario")
    first_name = serializers.CharField(help_text="Nombre del usuario")
    last_name = serializers.CharField(help_text="Apellido del usuario")
    phone_number = serializers.CharField(help_text="Número de teléfono")
    is_active = serializers.BooleanField(help_text="Usuario activo")
    approved_at = serializers.DateTimeField(allow_null=True, help_text="Fecha de aprobación")

class PhoneVerificationCheckResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de verificación exitosa"""
    message = serializers.CharField(help_text="Mensaje de confirmación")
    token = serializers.CharField(help_text="Token de autenticación del usuario")
    user = UserInfoResponseSerializer(help_text="Información del usuario autenticado")

# ============================================================================
# SERIALIZERS PARA POLÍTICA DE PRIVACIDAD
# ============================================================================

class PrivacyPolicySerializer(serializers.ModelSerializer):
    """Serializer para gestión de políticas de privacidad"""
    file_name = serializers.CharField(source='content.name', read_only=True, help_text="Nombre del archivo")
    file_size = serializers.SerializerMethodField(help_text="Tamaño del archivo en bytes")
    file_url = serializers.SerializerMethodField(help_text="URL para descargar el archivo")
    
    class Meta:
        model = PrivacyPolicy
        fields = [
            'id', 'content', 'file_name', 'file_size', 'file_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_name', 'file_size', 'file_url']
    
    def get_file_size(self, obj):
        """Obtener el tamaño del archivo en bytes"""
        if obj.content:
            try:
                return obj.content.size
            except (OSError, ValueError):
                return None
        return None
    
    def get_file_url(self, obj):
        """Obtener la URL para descargar el archivo"""
        if obj.content:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.content.url)
            return obj.content.url
        return None
    
    def validate_content(self, value):
        """Validar que el archivo sea un PDF"""
        if value:
            # Verificar extensión
            if not value.name.lower().endswith('.pdf'):
                raise serializers.ValidationError("Solo se permiten archivos PDF")
            
            # Verificar tamaño (máximo 10MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("El archivo no puede ser mayor a 10MB")
        
        return value

class PrivacyPolicyUploadSerializer(serializers.ModelSerializer):
    """Serializer para subida de política de privacidad"""
    
    class Meta:
        model = PrivacyPolicy
        fields = ['content']
    
    def validate_content(self, value):
        """Validar el archivo PDF"""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Solo se permiten archivos PDF")
        
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("El archivo no puede ser mayor a 10MB")
        
        return value

class PrivacyPolicyResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de operaciones con política de privacidad"""
    message = serializers.CharField(help_text="Mensaje descriptivo")
    data = PrivacyPolicySerializer(required=False, allow_null=True, help_text="Datos de la política de privacidad")

# ============================================================================
# SERIALIZERS PARA OPERACIONES MASIVAS
# ============================================================================

class BulkPreRegisterApprovalSerializer(serializers.Serializer):
    """Serializer para aprobación masiva de pre-registros"""
    pre_register_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Lista de IDs de pre-registros a aprobar"
    )
    
    def validate_pre_register_ids(self, value):
        if not value:
            raise serializers.ValidationError("La lista de IDs no puede estar vacía")
        return value

class BulkOperationResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de operaciones masivas"""
    message = serializers.CharField(help_text="Mensaje descriptivo de la operación")
    updated_count = serializers.IntegerField(help_text="Cantidad de registros actualizados")

class BulkUserDeactivationSerializer(serializers.Serializer):
    """Serializer para desactivación masiva de usuarios"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="Lista de IDs de usuarios a desactivar"
    )
    
    def validate_user_ids(self, value):
        if not value:
            raise serializers.ValidationError("La lista de IDs no puede estar vacía")
        return value
