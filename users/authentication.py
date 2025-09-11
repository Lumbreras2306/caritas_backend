# users/authentication.py
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from .models import CustomUserToken, AdminUser, CustomUser


class CustomTokenAuthentication(TokenAuthentication):
    """
    Autenticación personalizada que soporta tokens tanto para AdminUser como para CustomUser.
    Permite acceso a todos los endpoints con cualquier tipo de token válido.
    """
    
    def authenticate_credentials(self, key):
        """
        Autentica las credenciales del token.
        Busca primero en CustomUserToken, luego en Token estándar (AdminUser).
        """
        try:
            # Primero intentar con CustomUserToken
            custom_token = CustomUserToken.objects.select_related('user').get(key=key)
            user = custom_token.user
            
            # Verificar que el usuario esté activo
            if not user.is_active:
                return None
                
            return (user, custom_token)
            
        except CustomUserToken.DoesNotExist:
            try:
                # Si no se encuentra en CustomUserToken, intentar con Token estándar (AdminUser)
                token = Token.objects.select_related('user').get(key=key)
                user = token.user
                
                # Verificar que el usuario esté activo
                if not user.is_active:
                    return None
                    
                return (user, token)
                
            except Token.DoesNotExist:
                return None
    
    def get_user(self, token):
        """
        Obtiene el usuario asociado al token.
        """
        if isinstance(token, CustomUserToken):
            return token.user
        elif isinstance(token, Token):
            return token.user
        return None
