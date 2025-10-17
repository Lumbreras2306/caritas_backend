# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import CustomUserToken
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os

from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, 
    OpenApiResponse, OpenApiExample, OpenApiTypes
)

from .models import CustomUser, PreRegisterUser, AdminUser, PrivacyPolicy, STATUS_CHOICES
from .serializers import (
    CustomUserSerializer, PreRegisterUserSerializer, AdminUserSerializer,
    AdminUserLoginSerializer, AdminUserPasswordChangeSerializer, 
    PreRegisterVerificationSerializer, PhoneVerificationSendSerializer,
    PhoneVerificationCheckSerializer, BulkPreRegisterApprovalSerializer,
    BulkUserDeactivationSerializer, ErrorResponseSerializer,
    SuccessResponseSerializer, TokenResponseSerializer,
    PreRegisterVerificationResponseSerializer, PhoneVerificationSendResponseSerializer,
    PhoneVerificationCheckResponseSerializer, BulkOperationResponseSerializer,
    PrivacyPolicySerializer, PrivacyPolicyUploadSerializer, PrivacyPolicyResponseSerializer
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
            OpenApiParameter(
                name='status', 
                type=OpenApiTypes.STR, 
                enum=['PENDING', 'APPROVED', 'REJECTED'],
                description="Filtrar por estado del pre-registro"
            ),
            OpenApiParameter(
                name='gender', 
                type=OpenApiTypes.STR, 
                enum=['M', 'F'],
                description="Filtrar por género"
            ),
            OpenApiParameter(
                name='search', 
                type=OpenApiTypes.STR, 
                description='Busca en nombre, apellido, teléfono'
            ),
        ],
        responses={
            200: PreRegisterUserSerializer(many=True),
            401: ErrorResponseSerializer,
        }
    ),
    create=extend_schema(
        tags=['Pre-Register Users'],
        summary="Crear pre-registro",
        description="Crea un nuevo pre-registro de usuario. No requiere autenticación.",
        request=PreRegisterUserSerializer,
        responses={
            201: PreRegisterUserSerializer,
            400: ErrorResponseSerializer,
        },
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
                },
                request_only=True,
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Pre-Register Users'], 
        summary="Detalle de pre-registro",
        responses={200: PreRegisterUserSerializer, 404: ErrorResponseSerializer}
    ),
    update=extend_schema(
        tags=['Pre-Register Users'], 
        summary="Actualizar pre-registro",
        responses={200: PreRegisterUserSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=['Pre-Register Users'], 
        summary="Actualizar pre-registro parcial",
        responses={200: PreRegisterUserSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        tags=['Pre-Register Users'], 
        summary="Eliminar pre-registro",
        responses={204: None, 404: ErrorResponseSerializer}
    ),
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
        if self.action in ['create', 'verify_phone']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        instance = serializer.save()
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        if hasattr(self.request, 'user') and self.request.user and hasattr(self.request.user, 'is_authenticated') and self.request.user.is_authenticated:
            instance.updated_by = self.request.user
            instance.save()
        return instance

    @extend_schema(
        tags=['Pre-Register Users'],
        summary="Verificar teléfono",
        description="Verifica si existe un pre-registro con el número telefónico proporcionado",
        request=PreRegisterVerificationSerializer,
        responses={
            200: PreRegisterVerificationResponseSerializer,
            404: PreRegisterVerificationResponseSerializer,
            400: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'Verificar teléfono',
                value={"phone_number": "+52811908593"},
                request_only=True,
            ),
            OpenApiExample(
                'Pre-registro encontrado',
                value={
                    "exists": True,
                    "data": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "phone_number": "+52811908593",
                        "age": 25,
                        "gender": "M",
                        "status": "PENDING"
                    },
                    "message": "Pre-registro encontrado"
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
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
        request=BulkPreRegisterApprovalSerializer,
        responses={
            200: BulkOperationResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'Aprobar pre-registros',
                value={
                    "pre_register_ids": [
                        "123e4567-e89b-12d3-a456-426614174000",
                        "123e4567-e89b-12d3-a456-426614174001"
                    ]
                },
                request_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def approve(self, request):
        """Aprobar múltiples pre-registros."""
        serializer = BulkPreRegisterApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ids = serializer.validated_data['pre_register_ids']

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
        description="Obtiene lista paginada de usuarios finales del sistema",
        responses={200: CustomUserSerializer(many=True), 401: ErrorResponseSerializer}
    ),
    create=extend_schema(
        tags=['Custom Users'],
        summary="Crear usuario final",
        description="Crea un nuevo usuario final en el sistema",
        responses={201: CustomUserSerializer, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer}
    ),
    retrieve=extend_schema(
        tags=['Custom Users'], 
        summary="Detalle de usuario final",
        responses={200: CustomUserSerializer, 404: ErrorResponseSerializer}
    ),
    update=extend_schema(
        tags=['Custom Users'], 
        summary="Actualizar usuario final",
        responses={200: CustomUserSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=['Custom Users'], 
        summary="Actualizar usuario final parcial",
        responses={200: CustomUserSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        tags=['Custom Users'], 
        summary="Eliminar usuario final",
        responses={204: None, 404: ErrorResponseSerializer}
    ),
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
        instance = serializer.save(
            approved_by=self.request.user,
            approved_at=timezone.now(),
            created_by=self.request.user
        )
        return instance

    def perform_update(self, serializer):
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @extend_schema(
        tags=['Custom Users'],
        summary="Desactivar múltiples usuarios",
        description="Desactiva múltiples usuarios de forma masiva",
        request=BulkUserDeactivationSerializer,
        responses={
            200: BulkOperationResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        }
    )
    @action(detail=False, methods=['post'])
    def deactivate_multiple(self, request):
        """Desactivar múltiples usuarios."""
        serializer = BulkUserDeactivationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ids = serializer.validated_data['user_ids']

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
        description="Obtiene lista paginada de usuarios administradores",
        responses={200: AdminUserSerializer(many=True), 401: ErrorResponseSerializer}
    ),
    create=extend_schema(
        tags=['Admin Users'],
        summary="Crear administrador",
        description="Crea un nuevo usuario administrador",
        responses={201: AdminUserSerializer, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer}
    ),
    retrieve=extend_schema(
        tags=['Admin Users'], 
        summary="Detalle de administrador",
        responses={200: AdminUserSerializer, 404: ErrorResponseSerializer}
    ),
    update=extend_schema(
        tags=['Admin Users'], 
        summary="Actualizar administrador",
        responses={200: AdminUserSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=['Admin Users'], 
        summary="Actualizar administrador parcial",
        responses={200: AdminUserSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        tags=['Admin Users'], 
        summary="Eliminar administrador",
        responses={204: None, 404: ErrorResponseSerializer}
    ),
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
        if self.request.user.is_superuser:
            return AdminUser.objects.all()
        else:
            return AdminUser.objects.filter(id=self.request.user.id)

    @extend_schema(
        tags=['Admin Users'],
        summary="Cambiar contraseña",
        description="Cambia la contraseña del administrador actual",
        request=AdminUserPasswordChangeSerializer,
        responses={
            200: SuccessResponseSerializer,
            400: ErrorResponseSerializer,
        }
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

@extend_schema(tags=['Phone Verification'])
class PhoneVerificationViewSet(viewsets.ViewSet):
    """
    ViewSet para verificación de números de teléfono usando Twilio Verify.
    
    Permite enviar códigos SMS y verificarlos para autenticación
    de usuarios finales del sistema.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Enviar código SMS",
        description="Envía un código de verificación SMS usando Twilio Verify",
        request=PhoneVerificationSendSerializer,
        responses={
            200: PhoneVerificationSendResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'Enviar código',
                value={"phone_number": "+52811908593"},
                request_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
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
                    'error': 'Error al enviar el código de verificación',
                    'detail': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Verificar código SMS",
        description="Verifica el código SMS enviado al número de teléfono y retorna un token de autenticación si la verificación es exitosa.",
        request=PhoneVerificationCheckSerializer,
        responses={
            200: PhoneVerificationCheckResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'Verificar código',
                value={
                    "phone_number": "+52811908593",
                    "code": "123456"
                },
                request_only=True,
            ),
            OpenApiExample(
                'Verificación exitosa',
                value={
                    "message": "Código verificado exitosamente",
                    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                    "user": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "phone_number": "+52811908593",
                        "is_active": True,
                        "approved_at": "2024-01-15T10:30:00Z"
                    }
                },
                response_only=True,
            )
        ]
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
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
                        'error': 'No existe un usuario con este número de teléfono',
                        'detail': 'USER_NOT_FOUND'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'error': 'Código de verificación inválido',
                    'detail': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ============================================================================
# VISTAS DE AUTENTICACIÓN
# ============================================================================

@extend_schema(
    tags=['Authentication'],
    summary="Login de administrador",
    description="Autentica un administrador y retorna token de acceso",
    request=AdminUserLoginSerializer,
    responses={
        200: TokenResponseSerializer,
        400: ErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            'Login ejemplo',
            value={
                "username": "admin",
                "password": "password123"
            },
            request_only=True,
        ),
        OpenApiExample(
            'Login exitoso',
            value={
                "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "admin",
                "full_name": "Admin Usuario",
                "is_superuser": True,
                "main_hostel": "Casa San José"
            },
            response_only=True,
        )
    ]
)
class AdminUserLoginView(ObtainAuthToken):
    """
    Vista personalizada para login de administradores.
    
    Autentica administradores y genera tokens para acceso a la API.
    """
    serializer_class = AdminUserLoginSerializer
    permission_classes = [permissions.AllowAny]

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

@extend_schema(
    tags=['Authentication'],
    summary="Logout de administrador",
    description="Cierra la sesión de un administrador eliminando su token",
    responses={
        200: SuccessResponseSerializer,
        500: ErrorResponseSerializer,
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
                'error': 'Error al cerrar sesión',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Authentication'],
    summary="Obtener token estándar",
    description="Obtiene un token de autenticación usando el método estándar de DRF",
    request=AdminUserLoginSerializer,
    responses={
        200: TokenResponseSerializer,
        400: ErrorResponseSerializer,
    }
)
class CustomObtainAuthToken(ObtainAuthToken):
    """Vista personalizada para obtener token de autenticación con documentación."""
    permission_classes = [permissions.AllowAny]

@extend_schema(
    tags=['Authentication'],
    summary="Información del usuario autenticado",
    description="Obtiene información del usuario actualmente autenticado (AdminUser o CustomUser)",
    responses={
        200: OpenApiResponse(description="Información del usuario autenticado"),
        401: ErrorResponseSerializer,
    }
)
class UserInfoView(APIView):
    """Vista para obtener información del usuario autenticado."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener información del usuario autenticado."""
        user = request.user
        
        # Información común
        user_info = {
            'id': str(user.id),
            'is_authenticated': user.is_authenticated,
            'is_anonymous': getattr(user, 'is_anonymous', False),
            'is_active': user.is_active,
        }
        
        # Información específica según el tipo de usuario
        if isinstance(user, AdminUser):
            user_info.update({
                'user_type': 'admin',
                'username': user.username,
                'full_name': user.get_full_name(),
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'main_hostel': user.main_hostel.name if user.main_hostel else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            })
        elif isinstance(user, CustomUser):
            user_info.update({
                'user_type': 'custom',
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'phone_number': user.phone_number,
                'age': user.age,
                'gender': user.get_gender_display(),
                'poverty_level': user.get_poverty_level_display(),
                'approved_at': user.approved_at.isoformat() if user.approved_at else None,
                'approved_by': user.approved_by.get_full_name() if user.approved_by else None,
            })
        else:
            user_info.update({
                'user_type': 'unknown',
                'error': 'Tipo de usuario no reconocido'
            })
        
        return Response(user_info, status=status.HTTP_200_OK)

# ============================================================================
# VIEWSETS PARA POLÍTICA DE PRIVACIDAD
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Privacy Policy'],
        summary="Lista políticas de privacidad",
        description="Obtiene lista paginada de políticas de privacidad",
        responses={200: PrivacyPolicySerializer(many=True), 401: ErrorResponseSerializer}
    ),
    create=extend_schema(
        tags=['Privacy Policy'],
        summary="Crear política de privacidad",
        description="""
        Crea una nueva política de privacidad subiendo un archivo PDF.
        
        **Importante**: Este endpoint requiere enviar un archivo usando `multipart/form-data`.
        En Swagger UI, haz clic en "Try it out" y luego en "Choose File" para seleccionar tu archivo PDF.
        
        **Restricciones**:
        - Solo archivos PDF
        - Tamaño máximo: 10MB
        - Requiere autenticación de administrador
        """,
        request=PrivacyPolicyUploadSerializer,
        responses={
            201: PrivacyPolicyResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer
        },
        examples=[
            OpenApiExample(
                'Subir política de privacidad',
                summary="Ejemplo de subida de archivo",
                description="Selecciona un archivo PDF desde tu computadora",
                value={
                    "content": "archivo.pdf"
                },
                request_only=True,
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Privacy Policy'], 
        summary="Detalle de política de privacidad",
        responses={200: PrivacyPolicySerializer, 404: ErrorResponseSerializer}
    ),
    update=extend_schema(
        tags=['Privacy Policy'], 
        summary="Actualizar política de privacidad",
        request=PrivacyPolicyUploadSerializer,
        responses={200: PrivacyPolicyResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=['Privacy Policy'], 
        summary="Actualizar política de privacidad parcial",
        request=PrivacyPolicyUploadSerializer,
        responses={200: PrivacyPolicyResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}
    ),
    destroy=extend_schema(
        tags=['Privacy Policy'], 
        summary="Eliminar política de privacidad",
        responses={204: None, 404: ErrorResponseSerializer}
    ),
)
class PrivacyPolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de políticas de privacidad.
    
    Permite subir, descargar y gestionar archivos PDF de políticas de privacidad.
    Solo los administradores pueden gestionar estas políticas.
    """
    queryset = PrivacyPolicy.objects.all()
    serializer_class = PrivacyPolicySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Retornar el serializer apropiado según la acción"""
        if self.action in ['create', 'update', 'partial_update']:
            return PrivacyPolicyUploadSerializer
        return PrivacyPolicySerializer

    def perform_create(self, serializer):
        """Crear nueva política de privacidad"""
        instance = serializer.save()
        return instance

    def perform_update(self, serializer):
        """Actualizar política de privacidad"""
        instance = serializer.save()
        return instance

    @extend_schema(
        tags=['Privacy Policy'],
        summary="Descargar política de privacidad",
        description="Descarga el archivo PDF de la política de privacidad más reciente",
        responses={
            200: OpenApiResponse(description="Archivo PDF descargado"),
            404: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def download_latest(self, request):
        """Descargar la política de privacidad más reciente"""
        try:
            # Obtener la política más reciente
            latest_policy = PrivacyPolicy.objects.order_by('-created_at').first()
            
            if not latest_policy or not latest_policy.content:
                return Response({
                    'error': 'No hay política de privacidad disponible',
                    'detail': 'NO_POLICY_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Verificar que el archivo existe
            if not os.path.exists(latest_policy.content.path):
                return Response({
                    'error': 'El archivo de política de privacidad no existe',
                    'detail': 'FILE_NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Preparar respuesta con el archivo
            response = HttpResponse(
                latest_policy.content.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{latest_policy.content.name}"'
            response['Content-Length'] = latest_policy.content.size
            
            return response
            
        except Exception as e:
            return Response({
                'error': 'Error al descargar la política de privacidad',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=['Privacy Policy'],
        summary="Obtener política de privacidad actual",
        description="Obtiene información de la política de privacidad más reciente sin descargar el archivo",
        responses={
            200: PrivacyPolicySerializer,
            404: ErrorResponseSerializer,
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def current(self, request):
        """Obtener información de la política de privacidad actual"""
        try:
            latest_policy = PrivacyPolicy.objects.order_by('-created_at').first()
            
            if not latest_policy:
                return Response({
                    'error': 'No hay política de privacidad disponible',
                    'detail': 'NO_POLICY_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = PrivacyPolicySerializer(latest_policy, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Error al obtener la política de privacidad',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
