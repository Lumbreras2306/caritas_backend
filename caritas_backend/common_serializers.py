# caritas_backend/common_serializers.py
from rest_framework import serializers

# ============================================================================
# SERIALIZERS DE RESPUESTAS ESTÁNDAR COMPARTIDOS
# ============================================================================

class ErrorResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de error estándar"""
    error = serializers.CharField(help_text="Mensaje de error")
    detail = serializers.CharField(required=False, help_text="Detalle adicional del error")
    field_errors = serializers.DictField(required=False, help_text="Errores específicos por campo")

class SuccessResponseSerializer(serializers.Serializer):
    """Serializer para respuestas exitosas estándar"""
    message = serializers.CharField(help_text="Mensaje de éxito")
    data = serializers.DictField(required=False, help_text="Datos adicionales")

class BulkOperationResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de operaciones masivas"""
    message = serializers.CharField(help_text="Mensaje descriptivo de la operación")
    updated_count = serializers.IntegerField(help_text="Cantidad de registros actualizados")