from django.db import models
from users.models import AuditModel, FlexibleAuditModel
from albergues.models import Hostel
import uuid

########################################################
# MODELOS DE INVENTARIO
########################################################

class Item(AuditModel):
    """
    Modelo para objetos/artículos que pueden estar en inventarios.
    Los items se comparten entre inventarios para evitar duplicados.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nombre del artículo")
    description = models.TextField(
        blank=True, 
        verbose_name="Descripción",
        help_text="Descripción detallada del artículo"
    )
    category = models.CharField(
        max_length=100, 
        verbose_name="Categoría",
        help_text="Categoría del artículo (ej: Higiene, Alimentos, Limpieza)"
    )
    unit = models.CharField(
        max_length=50, 
        verbose_name="Unidad de medida",
        help_text="Unidad de medida (ej: piezas, paquetes, kg, litros)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.unit}"

    def get_total_quantity_in_inventory(self, inventory_id):
        """Retorna la cantidad total de este item en un inventario específico"""
        return self.inventory_items.filter(
            inventory_id=inventory_id,
            is_active=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

class Inventory(AuditModel):
    """
    Modelo para inventarios de albergues.
    Cada albergue tiene su propio inventario.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hostel = models.OneToOneField(
        Hostel,
        on_delete=models.CASCADE,
        verbose_name="Albergue",
        related_name="inventory"
    )
    name = models.CharField(
        max_length=255, 
        verbose_name="Nombre del inventario",
        help_text="Nombre descriptivo del inventario (ej: Inventario Principal)"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Descripción",
        help_text="Descripción del inventario"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    last_updated = models.DateTimeField(
        auto_now=True, 
        verbose_name="Última actualización"
    )

    class Meta:
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['hostel']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        return f"Inventario de {self.hostel.name}"

    def get_total_items(self):
        """Retorna el número total de artículos diferentes en el inventario"""
        return self.inventory_items.filter(is_active=True).count()

    def get_total_quantity(self):
        """Retorna la cantidad total de todos los artículos en el inventario"""
        total = sum(item.quantity for item in self.inventory_items.filter(is_active=True))
        return total

    def get_low_stock_items(self, threshold=5):
        """Retorna artículos con stock bajo (menos del umbral especificado)"""
        return self.inventory_items.filter(
            quantity__lte=threshold,
            is_active=True
        ).select_related('item')

    def get_empty_stock_items(self):
        """Retorna artículos sin stock (cantidad = 0)"""
        return self.inventory_items.filter(
            quantity=0,
            is_active=True
        ).select_related('item')


class InventoryItem(AuditModel):
    """
    Modelo para la relación entre inventario, artículo y cantidad.
    Permite que cada albergue tenga cantidades independientes del mismo artículo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        verbose_name="Inventario",
        related_name="inventory_items"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name="Artículo",
        related_name="inventory_items"
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad",
        help_text="Cantidad disponible del artículo en este inventario"
    )
    minimum_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock mínimo",
        help_text="Cantidad mínima recomendada para mantener en stock"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Artículo de inventario"
        verbose_name_plural = "Artículos de inventario"
        ordering = ['item__category', 'item__name']
        unique_together = ['inventory', 'item']
        indexes = [
            models.Index(fields=['inventory', 'item']),
            models.Index(fields=['quantity']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.item.name} - {self.quantity} {self.item.unit} en {self.inventory.hostel.name}"

    def is_low_stock(self):
        """Retorna True si el stock está por debajo del mínimo"""
        return self.quantity <= self.minimum_stock

    def is_out_of_stock(self):
        """Retorna True si no hay stock disponible"""
        return self.quantity == 0

    def get_stock_status(self):
        """Retorna el estado del stock como string"""
        if self.quantity == 0:
            return "Sin stock"
        elif self.is_low_stock():
            return "Stock bajo"
        else:
            return "Stock normal"

    def add_quantity(self, amount):
        """Añade cantidad al stock"""
        if amount > 0:
            self.quantity += amount
            self.save()
            return True
        return False

    def remove_quantity(self, amount):
        """Remueve cantidad del stock"""
        if amount > 0 and self.quantity >= amount:
            self.quantity -= amount
            self.save()
            return True
        return False

    def set_quantity(self, amount):
        """Establece la cantidad del stock"""
        if amount >= 0:
            self.quantity = amount
            self.save()
            return True
        return False