# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import CustomUserToken
from rest_framework.authtoken.views import ObtainAuthToken
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction

from .models import CustomUser, PreRegisterUser, AdminUser, STATUS_CHOICES
from .serializers import (
    CustomUserSerializer, PreRegisterUserSerializer, AdminUserSerializer,
    AdminUserLoginSerializer, AdminUserPasswordChangeSerializer, 
    PreRegisterVerificationSerializer, PhoneVerificationSendSerializer,
    PhoneVerificationCheckSerializer
)
from .twilio_verify_service import twilio_verify_service

# ============================================================================
# VIEWSETS PARA USUARIOS PRE-REGISTRO
# ============================================================================

class PreRegisterUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios pre-registro.
    
    Endpoints:
    - GET /api/users/pre-register/ - Lista todos los pre-registros
    - POST /api/users/pre-register/ - Crear nuevo pre-registro
    - GET /api/users/pre-register/{id}/ - Detalle de pre-registro
    - PUT/PATCH /api/users/pre-register/{id}/ - Actualizar status
    - DELETE /api/users/pre-register/{id}/ - Eliminar pre-registro
    - POST /api/users/pre-register/verify-phone/ - Verificar si existe preregistro por teléfono
    - POST /api/users/pre-register/approve/ - Aprobar múltiples pre-registros
    """
    queryset = PreRegisterUser.objects.all()
    serializer_class = PreRegisterUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'gender', 'age']
    search_fields = ['first_name', 'last_name', 'phone_number']
    ordering_fields = ['created_at', 'first_name', 'last_name', 'age']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Permisos personalizados por acción.
        """
        if self.action == 'create':
            # Permitir creación sin autenticación (registro público)
            permission_classes = [permissions.AllowAny]
        elif self.action in ['verify_phone']:
            # Permitir verificación sin autenticación
            permission_classes = [permissions.AllowAny]
        else:
            # Requiere autenticación para otras acciones
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Personalizar creación de pre-registro"""
        instance = serializer.save()
        # Aquí podrías agregar lógica adicional como enviar notificaciones
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de pre-registro"""
        instance = serializer.save()
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # Registrar quién modificó el registro
            instance.updated_by = self.request.user
            instance.save()
        return instance

    @action(detail=False, methods=['post'])
    def verify_phone(self, request):
        """
        Verificar si existe un preregistro con el número telefónico proporcionado.
        
        POST /api/users/pre-register/verify-phone/
        Body: {"phone_number": "+52 1234567890"}
        """
        serializer = PreRegisterVerificationSerializer(data=request.data)
        if serializer.is_valid():
            pre_register_data = serializer.get_pre_register_data()
            
            if pre_register_data:
                return Response({
                    'exists': True,
                    'data': pre_register_data,
                    'message': 'Pre-registro encontrado'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'exists': False,
                    'data': None,
                    'message': 'No se encontró pre-registro con este número'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def approve_multiple(self, request):
        """
        Aprobar múltiples pre-registros.
        
        POST /api/users/pre-register/approve/
        Body: {"ids": ["uuid1", "uuid2", "uuid3"]}
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'Se requiere una lista de IDs'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                pre_registers = PreRegisterUser.objects.filter(id__in=ids)
                updated_count = pre_registers.update(
                    status=STATUS_CHOICES.APPROVED,
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
                return Response({
                    'message': f'{updated_count} pre-registros aprobados exitosamente',
                    'updated_count': updated_count
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error al aprobar pre-registros: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ============================================================================
# VIEWSETS PARA USUARIOS FINALES
# ============================================================================

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios finales.
    
    Endpoints:
    - GET /api/users/customers/ - Lista todos los usuarios
    - POST /api/users/customers/ - Crear nuevo usuario
    - GET /api/users/customers/{id}/ - Detalle de usuario
    - PUT/PATCH /api/users/customers/{id}/ - Actualizar usuario
    - DELETE /api/users/customers/{id}/ - Eliminar usuario
    - POST /api/users/customers/deactivate-multiple/ - Desactivar múltiples usuarios
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'is_active', 'poverty_level']
    search_fields = ['first_name', 'last_name', 'phone_number']
    ordering_fields = ['created_at', 'first_name', 'last_name', 'age', 'approved_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Personalizar creación de usuario"""
        instance = serializer.save(
            approved_by=self.request.user,
            approved_at=timezone.now(),
            created_by=self.request.user
        )
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de usuario"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @action(detail=False, methods=['post'])
    def deactivate_multiple(self, request):
        """
        Desactivar múltiples usuarios.
        
        POST /api/users/customers/deactivate-multiple/
        Body: {"ids": ["uuid1", "uuid2", "uuid3"]}
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'Se requiere una lista de IDs'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                users = CustomUser.objects.filter(id__in=ids)
                updated_count = users.update(
                    is_active=False,
                    deactivated_by=request.user,
                    deactivated_at=timezone.now(),
                    updated_by=request.user,
                    updated_at=timezone.now()
                )
                
                return Response({
                    'message': f'{updated_count} usuarios desactivados exitosamente',
                    'updated_count': updated_count
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Error al desactivar usuarios: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ============================================================================
# VIEWSETS PARA ADMINISTRADORES
# ============================================================================

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios administradores.
    
    Endpoints:
    - GET /api/users/admins/ - Lista todos los administradores
    - POST /api/users/admins/ - Crear nuevo administrador
    - GET /api/users/admins/{id}/ - Detalle de administrador
    - PUT/PATCH /api/users/admins/{id}/ - Actualizar administrador
    - DELETE /api/users/admins/{id}/ - Eliminar administrador
    - POST /api/users/admins/change-password/ - Cambiar contraseña
    """
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'username', 'first_name', 'last_name', 'last_login']
    ordering = ['-created_at']

    def get_permissions(self):
        """
        Solo superusuarios pueden gestionar administradores.
        """
        permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Los superusuarios ven todos, otros solo se ven a sí mismos.
        """
        if self.request.user.is_superuser:
            return AdminUser.objects.all()
        else:
            return AdminUser.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Cambiar contraseña del administrador actual.
        
        POST /api/users/admins/change-password/
        Body: {
            "old_password": "contraseña_actual",
            "new_password": "nueva_contraseña",
            "new_password_confirm": "nueva_contraseña"
        }
        """
        serializer = AdminUserPasswordChangeSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Contraseña cambiada exitosamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VIEWSETS PARA CÓDIGOS OTP
# ============================================================================

class PhoneVerificationViewSet(viewsets.ViewSet):
    """
    ViewSet para verificación de números de teléfono usando Twilio Verify.
    
    Endpoints:
    - POST /api/users/phone-verification/send/ - Enviar código de verificación SMS
    - POST /api/users/phone-verification/verify/ - Verificar código SMS y obtener token
    """
    permission_classes = [permissions.AllowAny]  # Permitir acceso sin autenticación para estos endpoints

    @action(detail=False, methods=['post'])
    def send(self, request):
        """
        Enviar código de verificación SMS usando Twilio Verify.
        
        POST /api/users/phone-verification/send/
        Body: {"phone_number": "+52 1234567890"}
        """
        serializer = PhoneVerificationSendSerializer(data=request.data)
        
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
            # Enviar verificación usando Twilio Verify
            result = twilio_verify_service.send_verification(phone_number)
            
            if result['success']:
                return Response({
                    'message': 'Código de verificación enviado exitosamente',
                    'phone_number': phone_number,
                    'verification_sid': result['verification_sid']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Error al enviar el código de verificación',
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Verificar código SMS y retornar token de autenticación.
        
        POST /api/users/phone-verification/verify/
        Body: {
            "phone_number": "+52 1234567890",
            "code": "123456"
        }
        """
        serializer = PhoneVerificationCheckSerializer(data=request.data)
        
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            code = serializer.validated_data['code']
            
            # Verificar código usando Twilio Verify
            result = twilio_verify_service.check_verification(phone_number, code)
            
            if result['success']:
                # Buscar el usuario por número de teléfono
                try:
                    user = CustomUser.objects.get(phone_number=phone_number)
                    
                    # Crear o obtener token de autenticación personalizado para CustomUser
                    token, created = CustomUserToken.objects.get_or_create(user=user)
                    
                    return Response({
                        'message': 'Código verificado exitosamente',
                        'token': token.key,
                        'user': {
                            'id': user.id,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'phone_number': user.phone_number,
                            'is_active': user.is_active,
                            'approved_at': user.approved_at.isoformat() if user.approved_at else None
                        }
                    }, status=status.HTTP_200_OK)
                    
                except CustomUser.DoesNotExist:
                    return Response({
                        'message': 'No existe un usuario con este número de teléfono',
                        'error': 'USER_NOT_FOUND'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'message': 'Código de verificación inválido',
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VISTAS DE AUTENTICACIÓN
# ============================================================================

class AdminUserLoginView(ObtainAuthToken):
    """
    Vista personalizada para login de administradores.
    
    POST /api/users/auth/admin-login/
    Body: {
        "username": "admin",
        "password": "password"
    }
    """
    serializer_class = AdminUserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            # Actualizar último acceso
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'full_name': user.get_full_name(),
                'is_superuser': user.is_superuser,
                'main_hostel': user.main_hostel.name if user.main_hostel else None
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserLogoutView(viewsets.GenericViewSet):
    """
    Vista para logout de administradores.
    
    POST /api/users/auth/admin-logout/
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Cerrar sesión del administrador.
        """
        try:
            # Eliminar token
            request.user.auth_token.delete()
            return Response({
                'message': 'Sesión cerrada exitosamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Error al cerrar sesión'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
