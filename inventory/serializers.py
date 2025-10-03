# serializers.py
from rest_framework import serializers
from typing import Dict, Any, Optional
from .models import Item, Inventory, InventoryItem
from albergues.models import Hostel

# ============================================================================
# SERIALIZERS DE RESPUESTAS ESTÁNDAR
# ============================================================================

class ErrorResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de error estándar"""
    error = serializers.CharField(help_text="Mensaje de error")
    detail = serializers.CharField(required=False, help_text="Detalle adicional del error")

class SuccessResponseSerializer(serializers.Serializer):
    """Serializer para respuestas exitosas estándar"""
    message = serializers.CharField(help_text="Mensaje de éxito")
    data = serializers.DictField(required=False, help_text="Datos adicionales")

class BulkOperationResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de operaciones masivas"""
    message = serializers.CharField(help_text="Mensaje descriptivo de la operación")
    updated_count = serializers.IntegerField(help_text="Cantidad de registros actualizados")

# ============================================================================
# SERIALIZERS PARA ARTÍCULOS
# ============================================================================

class ItemSerializer(serializers.ModelSerializer):
    """Serializer para artículos"""
    total_inventories = serializers.SerializerMethodField()
    total_quantity_all_inventories = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Item
        fields = [
            'id', 'name', 'description', 'category', 'unit', 'is_active',
            'total_inventories', 'total_quantity_all_inventories',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_inventories', 'total_quantity_all_inventories',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_total_inventories(self, obj) -> int:
        """Retorna el número de inventarios que tienen este artículo"""
        return obj.inventory_items.filter(is_active=True).count()
    
    def get_total_quantity_all_inventories(self, obj) -> int:
        """Retorna la cantidad total de este artículo en todos los inventarios"""
        return sum(
            item.quantity for item in obj.inventory_items.filter(is_active=True)
        )

# ============================================================================
# SERIALIZERS PARA INVENTARIOS
# ============================================================================

class InventorySerializer(serializers.ModelSerializer):
    """Serializer para inventarios"""
    hostel_name = serializers.CharField(source='hostel.name', read_only=True)
    hostel_location = serializers.CharField(source='hostel.get_formatted_address', read_only=True)
    total_items = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    low_stock_count = serializers.SerializerMethodField()
    empty_stock_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'hostel', 'hostel_name', 'hostel_location', 'name', 'description', 
            'is_active', 'last_updated', 'total_items', 'total_quantity',
            'low_stock_count', 'empty_stock_count',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'hostel_name', 'hostel_location', 'last_updated',
            'total_items', 'total_quantity', 'low_stock_count', 'empty_stock_count',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_total_items(self, obj) -> int:
        """Retorna el número total de artículos diferentes"""
        return obj.get_total_items()
    
    def get_total_quantity(self, obj) -> int:
        """Retorna la cantidad total de todos los artículos"""
        return obj.get_total_quantity()
    
    def get_low_stock_count(self, obj) -> int:
        """Retorna el número de artículos con stock bajo"""
        return obj.get_low_stock_items().count()
    
    def get_empty_stock_count(self, obj) -> int:
        """Retorna el número de artículos sin stock"""
        return obj.get_empty_stock_items().count()
    
    def validate_hostel(self, value):
        """Validar que el albergue no tenga ya un inventario"""
        if self.instance is None:  # Solo en creación
            if Inventory.objects.filter(hostel=value).exists():
                raise serializers.ValidationError(
                    "Este albergue ya tiene un inventario asociado"
                )
        return value

# ============================================================================
# SERIALIZERS PARA ARTÍCULOS DE INVENTARIO
# ============================================================================

class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer para artículos de inventario"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_category = serializers.CharField(source='item.category', read_only=True)
    item_unit = serializers.CharField(source='item.unit', read_only=True)
    item_description = serializers.CharField(source='item.description', read_only=True)
    inventory_name = serializers.CharField(source='inventory.name', read_only=True)
    hostel_name = serializers.CharField(source='inventory.hostel.name', read_only=True)
    stock_status = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    is_out_of_stock = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'inventory', 'inventory_name', 'hostel_name',
            'item', 'item_name', 'item_category', 'item_unit', 'item_description',
            'quantity', 'minimum_stock', 'is_active',
            'stock_status', 'is_low_stock', 'is_out_of_stock',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'inventory_name', 'hostel_name', 'item_name', 'item_category',
            'item_unit', 'item_description', 'stock_status', 'is_low_stock', 'is_out_of_stock',
            'created_by_name', 'created_at', 'updated_at'
        ]
    
    def get_stock_status(self, obj) -> str:
        """Retorna el estado del stock"""
        return obj.get_stock_status()
    
    def get_is_low_stock(self, obj) -> bool:
        """Retorna si el stock está bajo"""
        return obj.is_low_stock()
    
    def get_is_out_of_stock(self, obj) -> bool:
        """Retorna si no hay stock"""
        return obj.is_out_of_stock()
    
    def validate(self, attrs):
        """Validar que no se duplique artículo en el mismo inventario"""
        inventory = attrs.get('inventory')
        item = attrs.get('item')
        
        if inventory and item:
            existing = InventoryItem.objects.filter(inventory=inventory, item=item)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError(
                    "Este artículo ya existe en el inventario seleccionado"
                )
        
        return attrs

class InventoryItemQuantityUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar solo cantidades de artículos"""
    action = serializers.ChoiceField(
        choices=['set', 'add', 'remove'],
        write_only=True,
        help_text="Acción a realizar: 'set' (establecer), 'add' (añadir), 'remove' (quitar)"
    )
    amount = serializers.IntegerField(
        write_only=True,
        min_value=0,
        help_text="Cantidad para la acción"
    )
    
    class Meta:
        model = InventoryItem
        fields = ['quantity', 'action', 'amount']
        read_only_fields = ['quantity']
    
    def validate_amount(self, value):
        """Validar que la cantidad sea válida"""
        if value < 0:
            raise serializers.ValidationError("La cantidad debe ser positiva")
        return value
    
    def update(self, instance, validated_data):
        """Actualizar la cantidad según la acción especificada"""
        action = validated_data.get('action')
        amount = validated_data.get('amount')
        
        if action == 'set':
            success = instance.set_quantity(amount)
        elif action == 'add':
            success = instance.add_quantity(amount)
        elif action == 'remove':
            success = instance.remove_quantity(amount)
        else:
            raise serializers.ValidationError("Acción no válida")
        
        if not success:
            raise serializers.ValidationError(
                f"No se pudo {action} {amount} unidades. Verifique la cantidad disponible."
            )
        
        # Registrar quién modificó el artículo
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            instance.updated_by = request.user
            instance.save()
        
        return instance

class InventoryItemDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para artículos de inventario con toda la información"""
    item_data = ItemSerializer(source='item', read_only=True)
    inventory_data = InventorySerializer(source='inventory', read_only=True)
    stock_status = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    is_out_of_stock = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'inventory', 'inventory_data', 'item', 'item_data',
            'quantity', 'minimum_stock', 'is_active',
            'stock_status', 'is_low_stock', 'is_out_of_stock',
            'created_by_name', 'updated_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'inventory_data', 'item_data', 'stock_status', 'is_low_stock', 'is_out_of_stock',
            'created_by_name', 'updated_by_name', 'created_at', 'updated_at'
        ]
    
    def get_stock_status(self, obj) -> str:
        """Retorna el estado del stock"""
        return obj.get_stock_status()
    
    def get_is_low_stock(self, obj) -> bool:
        """Retorna si el stock está bajo"""
        return obj.is_low_stock()
    
    def get_is_out_of_stock(self, obj) -> bool:
        """Retorna si no hay stock"""
        return obj.is_out_of_stock()
