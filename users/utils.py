# users/utils.py
from rest_framework.authtoken.models import Token
from .models import CustomUserToken, AdminUser, CustomUser


def get_user_token(user):
    """
    Obtiene el token de cualquier tipo de usuario (AdminUser o CustomUser).
    
    Args:
        user: Instancia de AdminUser o CustomUser
        
    Returns:
        Token object o None si no se encuentra
    """
    if isinstance(user, AdminUser):
        try:
            return Token.objects.get(user=user)
        except Token.DoesNotExist:
            return None
    elif isinstance(user, CustomUser):
        try:
            return CustomUserToken.objects.get(user=user)
        except CustomUserToken.DoesNotExist:
            return None
    return None


def create_user_token(user):
    """
    Crea un token para cualquier tipo de usuario.
    
    Args:
        user: Instancia de AdminUser o CustomUser
        
    Returns:
        Token object creado
    """
    if isinstance(user, AdminUser):
        token, created = Token.objects.get_or_create(user=user)
        return token
    elif isinstance(user, CustomUser):
        token, created = CustomUserToken.objects.get_or_create(user=user)
        return token
    else:
        raise ValueError(f"Tipo de usuario no soportado: {type(user)}")


def delete_user_token(user):
    """
    Elimina el token de cualquier tipo de usuario.
    
    Args:
        user: Instancia de AdminUser o CustomUser
        
    Returns:
        bool: True si se eliminó, False si no existía
    """
    if isinstance(user, AdminUser):
        try:
            token = Token.objects.get(user=user)
            token.delete()
            return True
        except Token.DoesNotExist:
            return False
    elif isinstance(user, CustomUser):
        try:
            token = CustomUserToken.objects.get(user=user)
            token.delete()
            return True
        except CustomUserToken.DoesNotExist:
            return False
    return False


def get_user_from_token(token_key):
    """
    Obtiene el usuario a partir de una clave de token.
    
    Args:
        token_key: Clave del token
        
    Returns:
        User object o None si no se encuentra
    """
    # Buscar primero en CustomUserToken
    try:
        custom_token = CustomUserToken.objects.select_related('user').get(key=token_key)
        return custom_token.user
    except CustomUserToken.DoesNotExist:
        pass
    
    # Buscar en Token estándar (AdminUser)
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        pass
    
    return None


def is_admin_user(user):
    """
    Verifica si el usuario es un AdminUser.
    
    Args:
        user: Instancia de usuario
        
    Returns:
        bool: True si es AdminUser
    """
    return isinstance(user, AdminUser)


def is_custom_user(user):
    """
    Verifica si el usuario es un CustomUser.
    
    Args:
        user: Instancia de usuario
        
    Returns:
        bool: True si es CustomUser
    """
    return isinstance(user, CustomUser)
