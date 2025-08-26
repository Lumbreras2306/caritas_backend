# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, PreRegisterUser, AdminUser, OTPCode, STATUS_CHOICES, phone_regex
from django.utils import timezone
from django.db import models

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
    
    def create(self, validated_data):
        # Validar si el usuario ya existe
        user_exists = CustomUser.objects.filter(phone_number=validated_data['phone_number']).exists()
        if user_exists:
            raise serializers.ValidationError("El usuario ya existe, por favor inicie sesión")
        
        # Validar si el pre-registro ya existe
        pre_register = PreRegisterUser.objects.filter(phone_number=validated_data['phone_number'])
        if pre_register:
            if pre_register.status == STATUS_CHOICES.PENDING:
                raise serializers.ValidationError("El pre-registro esta pendiente de aprobación")
            elif pre_register.status == STATUS_CHOICES.APPROVED:
                raise serializers.ValidationError("El pre-registro ya fue aprobado")
            elif pre_register.status == STATUS_CHOICES.REJECTED:
                raise serializers.ValidationError("El pre-registro ya fue rechazado. Contacte al administrador para más información.")

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Verificar que solo se actualice el campo status
        disallowed_fields = set(validated_data.keys()) - {'status'}
        if disallowed_fields:
            raise serializers.ValidationError(
                f"No se permite actualizar los siguientes campos: {', '.join(disallowed_fields)}"
            )
        
        if 'status' in validated_data:
            instance.status = validated_data['status']
        instance.save()
        return instance

class PreRegisterVerificationSerializer(serializers.Serializer):
    """Serializer para verificar si existe un preregistro con un número telefónico"""
    phone_number = serializers.CharField(max_length=15, required=True)
    
    def validate_phone_number(self, value):
        # Validar formato del número telefónico
        if not phone_regex.match(value):
            raise serializers.ValidationError("El número telefónico debe estar en formato: '+XX XXXXXXXXXX'")
        return value
    
    def get_pre_register_data(self):
        """Retorna los datos del preregistro si existe, None si no existe"""
        phone_number = self.validated_data['phone_number']
        
        try:
            pre_register = PreRegisterUser.objects.get(phone_number=phone_number)
            return {
                'first_name': pre_register.first_name,
                'last_name': pre_register.last_name,
                'age': pre_register.age,
                'gender': pre_register.gender,
                'poverty_level': pre_register.poverty_level,
                'phone_number': pre_register.phone_number
            }
        except PreRegisterUser.DoesNotExist:
            return None

# ============================================================================
# SERIALIZERS PARA USUARIOS FINALES
# ============================================================================

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer unificado para CustomUser"""
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 
            'age', 'gender', 'poverty_level', 'is_active',
            'approved_at', 'approved_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'approved_at', 'approved_by_name', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Validar si el usuario ya existe
        user_exists = CustomUser.objects.filter(phone_number=validated_data['phone_number']).exists()
        if user_exists:
            raise serializers.ValidationError("El usuario ya existe, por favor inicie sesión")
        
        # Modificar el campo de status del pre-registro a aprobado
        pre_register = PreRegisterUser.objects.filter(phone_number=validated_data['phone_number'])
        if pre_register:
            pre_register.status = STATUS_CHOICES.APPROVED
            pre_register.save()
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Lógica personalizada para actualizar si es necesaria
        return super().update(instance, validated_data)

# ============================================================================
# SERIALIZERS PARA ADMINISTRADORES
# ============================================================================

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer unificado para AdminUser - compatible con ViewSets"""
    main_hostel_name = serializers.CharField(source='main_hostel.name', read_only=True)
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'main_hostel', 'main_hostel_name', 'is_active', 'is_staff', 
            'is_superuser', 'last_login', 'created_at', 'updated_at',
            'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        # Validar contraseñas solo si se están cambiando
        if 'password' in attrs and 'password_confirm' in attrs:
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs
    
    def create(self, validated_data):
        if 'password' in validated_data:
            validated_data.pop('password_confirm')
            password = validated_data.pop('password')
            user = AdminUser.objects.create_user(**validated_data)
            user.set_password(password)
            user.save()
            return user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Remover campos de contraseña si no se están actualizando
        validated_data.pop('password_confirm', None)
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class AdminUserPasswordChangeSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña de administrador"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Las nuevas contraseñas no coinciden")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta")
        return value

# ============================================================================
# SERIALIZERS PARA CÓDIGOS OTP
# ============================================================================

class OTPCodeSerializer(serializers.ModelSerializer):
    """Serializer unificado para OTPCode - compatible con ViewSets"""
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = OTPCode
        fields = [
            'id', 'user', 'user_phone', 'user_name', 'purpose', 'channel',
            'hashed_code', 'expires_at', 'consumed_at', 'attempts', 'max_attempts',
            'meta_ip', 'meta_ua', 'created_at'
        ]
        read_only_fields = ['id', 'user_phone', 'user_name', 'created_at']

class OTPCodeVerifySerializer(serializers.Serializer):
    """Serializer para verificar códigos OTP"""
    code = serializers.CharField(required=True)
    purpose = serializers.ChoiceField(choices=OTPCode.Purpose.choices, required=True)
    
    def validate(self, attrs):
        user = self.context['user']
        code = attrs['code']
        purpose = attrs['purpose']
        
        try:
            otp = OTPCode.objects.get(
                user=user,
                purpose=purpose,
                consumed_at__isnull=True,
                expires_at__gt=timezone.now(),
                attempts__lt=models.F('max_attempts')
            )
            
            # Aquí deberías verificar el código hasheado
            # Por ahora solo validamos que el OTP existe y es válido
            attrs['otp'] = otp
            return attrs
            
        except OTPCode.DoesNotExist:
            raise serializers.ValidationError("Código OTP inválido o expirado")

# ============================================================================
# SERIALIZERS DE AUTENTICACIÓN
# ============================================================================

class AdminUserLoginSerializer(serializers.Serializer):
    """Serializer para login de administradores"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Credenciales inválidas")
            if not user.is_active:
                raise serializers.ValidationError("Usuario desactivado")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Debe proporcionar username y password")
        
        return attrs