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

# DRF Spectacular imports para documentación automática
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample, extend_schema_serializer
from drf_spectacular.types import OpenApiTypes

from .models import CustomUser, PreRegisterUser, AdminUser, STATUS_CHOICES
from .serializers import (
    CustomUserSerializer, PreRegisterUserSerializer, AdminUserSerializer,
    AdminUserLoginSerializer, AdminUserPasswordChangeSerializer, 
    PreRegisterVerificationSerializer, PhoneVerificationSendSerializer,
    PhoneVerificationCheckSerializer, BulkPreRegisterApprovalSerializer,
    BulkUserDeactivationSerializer, VerificationSuccessResponseSerializer,
    VerificationErrorResponseSerializer, VerificationSuccessResponseDocSerializer,
    VerificationErrorResponseDocSerializer
)
from .twilio_verify_service import twilio_verify_service


# ============================================================================
# VIEWSETS PARA USUARIOS PRE-REGISTRO
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Pre-Register Users'],
        summary="Lista pre-registros",
        description="Obtiene lista paginada de pre-registros de usuarios con filtros y búsqueda",
        parameters=[
            OpenApiParameter(name='status', type=OpenApiTypes.STR, enum=['PENDING', 'APPROVED', 'REJECTED']),
            OpenApiParameter(name='gender', type=OpenApiTypes.STR, enum=['M', 'F']),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre, apellido, teléfono'),
        ]
    ),
    create=extend_schema(
        tags=['Pre-Register Users'],
        summary="Crear pre-registro",
        description="Crea un nuevo pre-registro de usuario. No requiere autenticación.",
        examples=[
            OpenApiExample(
                'Pre-registro ejemplo',
                value={
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "phone_number": "+52811908593",
                    "age": 25,
                    "gender": "M",
                    "privacy_policy_accepted": True
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Pre-Register Users'], summary="Detalle de pre-registro"),
    update=extend_schema(tags=['Pre-Register Users'], summary="Actualizar pre-registro"),
    partial_update=extend_schema(tags=['Pre-Register Users'], summary="Actualizar pre-registro parcial"),
    destroy=extend_schema(tags=['Pre-Register Users'], summary="Eliminar pre-registro"),
)
class PreRegisterUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios pre-registro.
    
    Los pre-registros son solicitudes de usuarios que requieren aprobación
    de un administrador antes de convertirse en usuarios activos del sistema.
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
        """Permisos personalizados por acción."""
        if self.action in ['create', 'verify_phone']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Personalizar creación de pre-registro"""
        instance = serializer.save()
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de pre-registro"""
        instance = serializer.save()
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            instance.updated_by = self.request.user
            instance.save()
        return instance

    @extend_schema(
        tags=['Pre-Register Users'],
        summary="Verificar teléfono",
        description="Verifica si existe un pre-registro con el número telefónico proporcionado",
        request=PreRegisterVerificationSerializer,
        responses={
            200: OpenApiResponse(description="Pre-registro encontrado"),
            404: OpenApiResponse(description="No se encontró pre-registro"),
        }
    )
    @action(detail=False, methods=['post'])
    def verify_phone(self, request):
        """Verificar si existe un preregistro con el número telefónico proporcionado."""
        serializer = PreRegisterVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
            try:
                pre_register = PreRegisterUser.objects.get(phone_number=phone_number)
                return Response({
                    'exists': True,
                    'data': PreRegisterUserSerializer(pre_register).data,
                    'message': 'Pre-registro encontrado'
                }, status=status.HTTP_200_OK)
            except PreRegisterUser.DoesNotExist:
                return Response({
                    'exists': False,
                    'data': None,
                    'message': 'No se encontró pre-registro con este número'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Pre-Register Users'],
        summary="Aprobar múltiples pre-registros",
        description="Aprueba múltiples pre-registros de forma masiva",
        request=BulkPreRegisterApprovalSerializer
    )
    @action(detail=False, methods=['post'])
    def approve(self, request):
        """Aprobar múltiples pre-registros."""
        ids = request.data.get('pre_register_ids', [])
        if not ids:
            return Response(
                {'error': 'Se requiere una lista de pre_register_ids'}, 
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

@extend_schema_view(
    list=extend_schema(
        tags=['Custom Users'],
        summary="Lista usuarios finales",
        description="Obtiene lista paginada de usuarios finales del sistema"
    ),
    create=extend_schema(
        tags=['Custom Users'],
        summary="Crear usuario final",
        description="Crea un nuevo usuario final en el sistema"
    ),
    retrieve=extend_schema(tags=['Custom Users'], summary="Detalle de usuario final"),
    update=extend_schema(tags=['Custom Users'], summary="Actualizar usuario final"),
    partial_update=extend_schema(tags=['Custom Users'], summary="Actualizar usuario final parcial"),
    destroy=extend_schema(tags=['Custom Users'], summary="Eliminar usuario final"),
)
class CustomUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios finales.
    
    Los usuarios finales son usuarios aprobados que pueden usar
    los servicios del sistema como reservar alojamiento y servicios.
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

    @extend_schema(
        tags=['Custom Users'],
        summary="Desactivar múltiples usuarios",
        description="Desactiva múltiples usuarios de forma masiva",
        request=BulkUserDeactivationSerializer
    )
    @action(detail=False, methods=['post'])
    def deactivate_multiple(self, request):
        """Desactivar múltiples usuarios."""
        ids = request.data.get('user_ids', [])
        if not ids:
            return Response(
                {'error': 'Se requiere una lista de user_ids'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                users = CustomUser.objects.filter(id__in=ids)
                updated_count = users.update(
                    is_active=False,
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

@extend_schema_view(
    list=extend_schema(
        tags=['Admin Users'],
        summary="Lista administradores",
        description="Obtiene lista paginada de usuarios administradores"
    ),
    create=extend_schema(
        tags=['Admin Users'],
        summary="Crear administrador",
        description="Crea un nuevo usuario administrador"
    ),
    retrieve=extend_schema(tags=['Admin Users'], summary="Detalle de administrador"),
    update=extend_schema(tags=['Admin Users'], summary="Actualizar administrador"),
    partial_update=extend_schema(tags=['Admin Users'], summary="Actualizar administrador parcial"),
    destroy=extend_schema(tags=['Admin Users'], summary="Eliminar administrador"),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios administradores.
    
    Los administradores tienen acceso completo al sistema de gestión
    y pueden crear/modificar usuarios, albergues, servicios, etc.
    """
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'username', 'first_name', 'last_name', 'last_login']
    ordering = ['-created_at']

    def get_queryset(self):
        """Los superusuarios ven todos, otros solo se ven a sí mismos."""
        if self.request.user.is_superuser:
            return AdminUser.objects.all()
        else:
            return AdminUser.objects.filter(id=self.request.user.id)

    @extend_schema(
        tags=['Admin Users'],
        summary="Cambiar contraseña",
        description="Cambia la contraseña del administrador actual",
        request=AdminUserPasswordChangeSerializer
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambiar contraseña del administrador actual."""
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
# VIEWSETS PARA VERIFICACIÓN DE TELÉFONO
# ============================================================================

class PhoneVerificationViewSet(viewsets.ViewSet):
    """
    ViewSet para verificación de números de teléfono usando Twilio Verify.
    
    Permite enviar códigos SMS y verificarlos para autenticación
    de usuarios finales del sistema.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Phone Verification'],
        summary="Enviar código SMS",
        description="Envía un código de verificación SMS usando Twilio Verify",
        request=PhoneVerificationSendSerializer,
        responses={
            200: OpenApiResponse(description="Código enviado exitosamente"),
            500: OpenApiResponse(description="Error al enviar código"),
        },
        examples=[
            OpenApiExample(
                'Enviar código',
                value={"phone_number": "+52811908593"}
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Enviar código de verificación SMS usando Twilio Verify."""
        serializer = PhoneVerificationSendSerializer(data=request.data)
        
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
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

    @extend_schema(
        tags=['Phone Verification'],
        summary="Verificar código SMS",
        description="Verifica el código SMS enviado al número de teléfono y retorna un token de autenticación si la verificación es exitosa. El token puede ser usado para autenticar futuras peticiones a la API.",
        request=PhoneVerificationCheckSerializer,
        responses={
            200: VerificationSuccessResponseDocSerializer,
            400: VerificationErrorResponseDocSerializer,
            404: VerificationErrorResponseDocSerializer,
        }
    )
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verificar código SMS y retornar token de autenticación."""
        serializer = PhoneVerificationCheckSerializer(data=request.data)
        
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            code = serializer.validated_data['code']
            
            result = twilio_verify_service.check_verification(phone_number, code)
            
            if result['success']:
                try:
                    user = CustomUser.objects.get(phone_number=phone_number)
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
    
    Autentica administradores y genera tokens para acceso a la API.
    """
    serializer_class = AdminUserLoginSerializer

    @extend_schema(
        tags=['Authentication'],
        summary="Login de administrador",
        description="Autentica un administrador y retorna token de acceso",
        request=AdminUserLoginSerializer,
        responses={
            200: OpenApiResponse(description="Login exitoso"),
            400: OpenApiResponse(description="Credenciales inválidas"),
        },
        examples=[
            OpenApiExample(
                'Login ejemplo',
                value={
                    "username": "admin",
                    "password": "password123"
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
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

from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken

@extend_schema(
    tags=['Authentication'],
    summary="Logout de administrador",
    description="Cierra la sesión de un administrador eliminando su token",
    responses={
        200: OpenApiResponse(description="Logout exitoso"),
        500: OpenApiResponse(description="Error al cerrar sesión"),
    }
)
class AdminUserLogoutView(APIView):
    """Vista para logout de administradores."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Cerrar sesión del administrador."""
        try:
            request.user.auth_token.delete()
            return Response({
                'message': 'Sesión cerrada exitosamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Error al cerrar sesión'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Authentication'],
    summary="Obtener token de autenticación",
    description="Obtiene un token de autenticación para usuarios administradores usando credenciales",
    responses={
        200: OpenApiResponse(description="Token generado exitosamente"),
        400: OpenApiResponse(description="Credenciales inválidas"),
    },
    examples=[
        OpenApiExample(
            'Obtener token',
            value={
                "username": "admin",
                "password": "password123"
            }
        )
    ]
)
class CustomObtainAuthToken(ObtainAuthToken):
    """Vista personalizada para obtener token de autenticación con documentación."""
    pass
