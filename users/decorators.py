# users/decorators.py
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .models import AdminUser, CustomUser


def require_admin_user(view_func):
    """
    Decorador para requerir que el usuario autenticado sea un AdminUser.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar autenticación de manera segura
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not isinstance(request.user, AdminUser):
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_custom_user(view_func):
    """
    Decorador para requerir que el usuario autenticado sea un CustomUser.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar autenticación de manera segura
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not isinstance(request.user, CustomUser):
            return Response(
                {'error': 'Custom user access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_any_authenticated_user(view_func):
    """
    Decorador para requerir cualquier usuario autenticado (AdminUser o CustomUser).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar autenticación de manera segura
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not isinstance(request.user, (AdminUser, CustomUser)):
            return Response(
                {'error': 'Invalid user type'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return view_func(request, *args, **kwargs)
    return wrapper
