# caritas_backend/hooks.py

def postprocess_schema_cleanup(result, generator, request, public):
    """
    Hook para limpiar esquemas de autenticación duplicados.
    Solo deja TokenAuth tal como lo definimos.
    """
    if 'components' in result and 'securitySchemes' in result['components']:
        # Guardar solo nuestro TokenAuth personalizado
        security_schemes = result['components']['securitySchemes']
        
        # Si existe TokenAuth, mantenerlo y eliminar todo lo demás
        if 'TokenAuth' in security_schemes:
            token_auth = security_schemes['TokenAuth']
            result['components']['securitySchemes'] = {
                'TokenAuth': token_auth
            }
    
    return result