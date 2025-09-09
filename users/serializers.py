# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import (
    CustomUser, PreRegisterUser, AdminUser, OTPCode, 
    STATUS_CHOICES, phone_regex
)

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
        read_only_fields = ['id', 'status', 'created_at']
    
    def validate_phone_number(self, value):
        """Validar número de teléfono"""
        if not phone_regex.match(value):
            raise serializers.ValidationError("El número de teléfono no es válido")
        return value
    
    def validate_age(self, value):
        """Validar edad"""
        if value < 18:
            raise serializers.ValidationError("Debe ser mayor de 18 años")
        if value > 100:
            raise serializers.ValidationError("Edad no válida")
        return value
    
    def create(self, validated_data):
        # Validar si el usuario ya existe
        user_exists = CustomUser.objects.filter(phone_number=validated_data['phone_number']).exists()
        if user_exists:
            raise serializers.ValidationError("El usuario ya existe, por favor contacte al administrador")
        
        # Validar si el pre-registro ya existe
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
        if not phone_regex.match(value):
            raise serializers.ValidationError("El número de teléfono no es válido")
        return value

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
        if not phone_regex.match(value):
            raise serializers.ValidationError("El número de teléfono no es válido")
        return value
    
    def validate_age(self, value):
        """Validar edad"""
        if value < 18:
            raise serializers.ValidationError("Debe ser mayor de 18 años")
        if value > 100:
            raise serializers.ValidationError("Edad no válida")
        return value
    
    def create(self, validated_data):
        # Validar si el usuario ya existe
        user_exists = CustomUser.objects.filter(phone_number=validated_data['phone_number']).exists()
        if user_exists:
            raise serializers.ValidationError("El usuario ya existe")
        
        # Modificar el campo de status del pre-registro a aprobado si existe
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
        # Validar contraseñas solo si se están cambiando
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
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
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
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
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
# SERIALIZERS PARA CÓDIGOS OTP
# ============================================================================

class OTPCodeSerializer(serializers.ModelSerializer):
    """Serializer básico para OTPCode"""
    
    class Meta:
        model = OTPCode
        fields = [
            'id', 'phone_number', 'is_used', 'expires_at',
            'attempts', 'max_attempts', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class OTPCodeVerifySerializer(serializers.Serializer):
    """Serializer para verificar código OTP"""
    phone_number = serializers.CharField(max_length=17, validators=[phone_regex])
    code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_phone_number(self, value):
        if not phone_regex.match(value):
            raise serializers.ValidationError("El número de teléfono no es válido")
        return value
    
    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El código debe contener solo números")
        return value