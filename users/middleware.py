# users/middleware.py
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class UserTypeMiddleware(MiddlewareMixin):
    """
    Middleware opcional para identificar el tipo de usuario autenticado.
    Útil para debugging y logging.
    """
    
    def process_request(self, request):
        """
        Agrega información del tipo de usuario al request para debugging.
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            from .models import AdminUser, CustomUser
            
            if isinstance(request.user, AdminUser):
                request.user_type = 'admin'
                logger.debug(f"AdminUser autenticado: {request.user.username}")
            elif isinstance(request.user, CustomUser):
                request.user_type = 'custom'
                logger.debug(f"CustomUser autenticado: {request.user.get_full_name()}")
            else:
                request.user_type = 'unknown'
                logger.warning(f"Tipo de usuario desconocido: {type(request.user)}")
        else:
            request.user_type = 'anonymous'
        
        return None
