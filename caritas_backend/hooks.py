# caritas_backend/hooks.py
from drf_spectacular.hooks import postprocess_schema_enums
from drf_spectacular.utils import OpenApiParameter


def custom_postprocessing_hook(result, generator, request, public):
    """
    Hook personalizado para postprocesar el esquema de OpenAPI.
    Elimina completamente esquemas de autenticación generados automáticamente y deja solo TokenAuth.
    """

    if 'components' in result:
        if 'securitySchemes' in result['components']:
            security_schemes = result['components']['securitySchemes']

            # Crear esquema completamente limpio
            clean_schemes = {}

            # Buscar TokenAuth exactamente como lo definimos en APPEND_COMPONENTS
            for scheme_name, scheme_data in security_schemes.items():
                if scheme_name == 'TokenAuth':
                    clean_schemes['TokenAuth'] = scheme_data
                    break

            # Reemplazar completamente el esquema de seguridad
            result['components']['securitySchemes'] = clean_schemes

    return result


def custom_preprocessing_hook(endpoints, **kwargs):
    """
    Hook personalizado para preprocesar los endpoints antes de generar el esquema.
    Esto nos permite controlar exactamente qué información se incluye en el esquema.
    """

    # Este hook se ejecuta antes de generar el esquema
    # Por ahora, simplemente retornamos los endpoints sin modificar
    # El control principal se hace en el postprocessing hook

    return endpoints
