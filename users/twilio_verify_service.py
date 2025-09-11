# users/twilio_verify_service.py
import os
import logging
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)

class TwilioVerifyService:
    """
    Servicio para manejar verificación de números de teléfono usando Twilio Verify
    
    Utiliza las variables oficiales de Twilio:
    - TWILIO_ACCOUNT_SID: Tu Account SID de Twilio
    - TWILIO_AUTH_TOKEN: Tu Auth Token de Twilio
    - TWILIO_VERIFY_SERVICE_SID: Tu Verify Service SID
    
    Basado en el patrón oficial de Twilio Functions
    """
    
    def __init__(self):
        # Usar las variables oficiales de Twilio
        # TWILIO_ACCOUNT_SID=SID
        # TWILIO_AUTH_TOKEN=TOKEN
        # TWILIO_VERIFY_SERVICE_SID=SERVICE_SID
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID") or getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN") or getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.verify_service_sid = os.environ.get("TWILIO_VERIFY_SERVICE_SID") or getattr(settings, 'TWILIO_VERIFY_SERVICE_SID', '')
        
        # Validar que las credenciales estén configuradas
        if not all([self.account_sid, self.auth_token, self.verify_service_sid]):
            logger.warning("Twilio credentials not fully configured. Some features may not work.")
        
        # Crear cliente usando Account SID y Auth Token (patrón oficial)
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
            self.client = None
    
    def send_verification(self, phone_number: str) -> dict:
        """
        Envía código de verificación SMS al número de teléfono usando Twilio Verify
        
        Args:
            phone_number (str): Número de teléfono destino en formato internacional (ej: +52811908593)
            
        Returns:
            dict: Resultado del envío con información de estado
        """
        if not self.client:
            return {
                'success': False,
                'verification_sid': None,
                'status': 'failed',
                'error': 'Twilio client not initialized'
            }
        
        try:
            # Usar el patrón oficial de Twilio Verify (basado en el ejemplo oficial)
            verification = self.client.verify.services(
                self.verify_service_sid
            ).verifications.create(
                to=phone_number,
                channel='sms',
                locale='es'
            )
            
            logger.info(f"Verificación SMS enviada a {phone_number}. SID: {verification.sid}")
            
            return {
                'success': True,
                'verification_sid': verification.sid,
                'status': verification.status,
                'error': None
            }
            
        except TwilioException as e:
            error_msg = f"Error de Twilio al enviar verificación a {phone_number}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'verification_sid': None,
                'status': 'failed',
                'error': str(e)
            }
        except Exception as e:
            error_msg = f"Error inesperado al enviar verificación a {phone_number}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'verification_sid': None,
                'status': 'failed',
                'error': str(e)
            }
    
    def check_verification(self, phone_number: str, code: str) -> dict:
        """
        Verifica el código OTP enviado al número de teléfono usando Twilio Verify
        
        Args:
            phone_number (str): Número de teléfono en formato internacional (ej: +52811908593)
            code (str): Código OTP a verificar (6 dígitos)
            
        Returns:
            dict: Resultado de la verificación con información de estado
        """
        if not self.client:
            return {
                'success': False,
                'verification_sid': None,
                'status': 'failed',
                'error': 'Twilio client not initialized'
            }
        
        try:
            # Usar el patrón oficial de Twilio Verify (basado en el ejemplo oficial)
            verification_check = self.client.verify.services(
                self.verify_service_sid
            ).verification_checks.create(
                to=phone_number,
                code=code
            )
            
            is_approved = verification_check.status == 'approved'
            logger.info(f"Verificación de código para {phone_number}. Status: {verification_check.status}")
            
            return {
                'success': is_approved,
                'verification_sid': verification_check.sid,
                'status': verification_check.status,
                'error': None if is_approved else 'Código inválido o expirado'
            }
            
        except TwilioException as e:
            error_msg = f"Error de Twilio al verificar código para {phone_number}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'verification_sid': None,
                'status': 'failed',
                'error': str(e)
            }
        except Exception as e:
            error_msg = f"Error inesperado al verificar código para {phone_number}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'verification_sid': None,
                'status': 'failed',
                'error': str(e)
            }
    
    def send_sms(self, to_phone: str, message: str, from_phone: str = None) -> dict:
        """
        Envía un SMS directo usando el patrón oficial de Twilio
        
        Args:
            to_phone (str): Número de teléfono destino en formato internacional (ej: +52811908593)
            message (str): Mensaje a enviar
            from_phone (str): Número de teléfono origen (opcional, usa el configurado en Twilio)
            
        Returns:
            dict: Resultado del envío con información del mensaje
        """
        if not self.client:
            return {
                'success': False,
                'message_sid': None,
                'status': 'failed',
                'error': 'Twilio client not initialized'
            }
        
        try:
            # Usar el patrón oficial de Twilio para enviar SMS
            message_obj = self.client.messages.create(
                to=to_phone,
                body=message,
                from_=from_phone  # Si no se especifica, usa el número configurado en Twilio
            )
            
            logger.info(f"SMS enviado a {to_phone}. SID: {message_obj.sid}")
            
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status,
                'error': None
            }
            
        except TwilioException as e:
            error_msg = f"Error de Twilio al enviar SMS a {to_phone}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message_sid': None,
                'status': 'failed',
                'error': str(e)
            }
        except Exception as e:
            error_msg = f"Error inesperado al enviar SMS a {to_phone}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message_sid': None,
                'status': 'failed',
                'error': str(e)
            }

# Instancia global del servicio
twilio_verify_service = TwilioVerifyService()
