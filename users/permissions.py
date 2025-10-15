# users/permissions.py
from rest_framework import permissions
from .models import AdminUser, CustomUser


class IsAdminUser(permissions.BasePermission):
    """
    Permiso personalizado que solo permite acceso a AdminUser.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return isinstance(request.user, AdminUser)


class IsCustomUser(permissions.BasePermission):
    """
    Permiso personalizado que solo permite acceso a CustomUser.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return isinstance(request.user, CustomUser)


class IsAdminOrCustomUser(permissions.BasePermission):
    """
    Permiso que permite acceso tanto a AdminUser como a CustomUser.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return isinstance(request.user, (AdminUser, CustomUser))


class CustomUserReadOnly(permissions.BasePermission):
    """
    Permiso que permite a CustomUser solo lectura, pero a AdminUser acceso completo.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if isinstance(request.user, AdminUser):
            return True
        elif isinstance(request.user, CustomUser):
            # CustomUser solo puede hacer GET, HEAD, OPTIONS
            return request.method in permissions.SAFE_METHODS
        
        return False


class CustomUserReservationAccess(permissions.BasePermission):
    """
    Permiso específico para reservas de CustomUser.
    Permite a CustomUser acceder solo a sus propias reservas.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if isinstance(request.user, AdminUser):
            return True
        elif isinstance(request.user, CustomUser):
            # CustomUser puede hacer GET, POST, PATCH en reservas
            return request.method in ['GET', 'POST', 'PATCH', 'HEAD', 'OPTIONS']
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica si el usuario puede acceder a un objeto específico.
        """
        if isinstance(request.user, AdminUser):
            return True
        elif isinstance(request.user, CustomUser):
            # CustomUser solo puede acceder a sus propias reservas
            if hasattr(obj, 'user') and obj.user == request.user:
                return True
        
        return False


class CustomUserHostelAccess(permissions.BasePermission):
    """
    Permiso específico para acceso a albergues por CustomUser.
    Permite solo lectura de albergues.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if isinstance(request.user, AdminUser):
            return True
        elif isinstance(request.user, CustomUser):
            # CustomUser solo puede hacer GET en albergues
            return request.method in ['GET', 'HEAD', 'OPTIONS']
        
        return False


class CustomUserServiceAccess(permissions.BasePermission):
    """
    Permiso específico para acceso a servicios por CustomUser.
    Permite solo lectura de servicios.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if isinstance(request.user, AdminUser):
            return True
        elif isinstance(request.user, CustomUser):
            # CustomUser solo puede hacer GET en servicios
            return request.method in ['GET', 'HEAD', 'OPTIONS']
        
        return False
