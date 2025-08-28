# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg

from .models import Item, Inventory, InventoryItem
from .serializers import (
    ItemSerializer, InventorySerializer, InventoryItemSerializer,
    InventoryItemQuantityUpdateSerializer, InventoryItemDetailSerializer
)

# ============================================================================
# VIEWSETS PARA ARTÍCULOS
# ============================================================================

class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de artículos.
    
    Endpoints:
    - GET /api/inventory/items/ - Lista todos los artículos
    - POST /api/inventory/items/ - Crear nuevo artículo
    - GET /api/inventory/items/{id}/ - Detalle de artículo
    - PUT/PATCH /api/inventory/items/{id}/ - Actualizar artículo
    - DELETE /api/inventory/items/{id}/ - Eliminar artículo
    - GET /api/inventory/items/categories/ - Lista de categorías únicas
    - GET /api/inventory/items/units/ - Lista de unidades únicas
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'unit', 'is_active']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['created_at', 'name', 'category']
    ordering = ['category', 'name']

    def perform_create(self, serializer):
        """Personalizar creación de artículo"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de artículo"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Lista todas las categorías únicas de artículos.
        
        GET /api/inventory/items/categories/
        """
        categories = Item.objects.values_list('category', flat=True).distinct().order_by('category')
        return Response({
            'categories': list(categories)
        })

    @action(detail=False, methods=['get'])
    def units(self, request):
        """
        Lista todas las unidades de medida únicas.
        
        GET /api/inventory/items/units/
        """
        units = Item.objects.values_list('unit', flat=True).distinct().order_by('unit')
        return Response({
            'units': list(units)
        })

# ============================================================================
# VIEWSETS PARA INVENTARIOS
# ============================================================================

class InventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de inventarios.
    
    Endpoints:
    - GET /api/inventory/inventories/ - Lista todos los inventarios
    - POST /api/inventory/inventories/ - Crear nuevo inventario
    - GET /api/inventory/inventories/{id}/ - Detalle de inventario
    - PUT/PATCH /api/inventory/inventories/{id}/ - Actualizar inventario
    - DELETE /api/inventory/inventories/{id}/ - Eliminar inventario
    - GET /api/inventory/inventories/{id}/summary/ - Resumen del inventario
    """
    queryset = Inventory.objects.select_related('hostel').all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hostel', 'is_active']
    search_fields = ['name', 'description', 'hostel__name']
    ordering_fields = ['created_at', 'last_updated', 'name']
    ordering = ['-last_updated']

    def perform_create(self, serializer):
        """Personalizar creación de inventario"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de inventario"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Resumen completo del inventario.
        
        GET /api/inventory/inventories/{id}/summary/
        """
        inventory = self.get_object()
        
        # Estadísticas básicas
        total_items = inventory.get_total_items()
        total_quantity = inventory.get_total_quantity()
        low_stock_items = inventory.get_low_stock_items()
        empty_stock_items = inventory.get_empty_stock_items()
        
        # Estadísticas por categoría
        items_by_category = inventory.inventory_items.filter(
            is_active=True
        ).values(
            'item__category'
        ).annotate(
            count=Count('id'),
            total_quantity=Sum('quantity'),
            avg_quantity=Avg('quantity')
        ).order_by('item__category')
        
        return Response({
            'inventory': {
                'id': inventory.id,
                'name': inventory.name,
                'hostel': inventory.hostel.name,
                'last_updated': inventory.last_updated
            },
            'summary': {
                'total_different_items': total_items,
                'total_quantity_all_items': total_quantity,
                'low_stock_count': low_stock_items.count(),
                'empty_stock_count': empty_stock_items.count()
            },
            'by_category': list(items_by_category)
        })

# ============================================================================
# VIEWSETS PARA ARTÍCULOS DE INVENTARIO
# ============================================================================

class InventoryItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de artículos en inventarios.
    
    Endpoints:
    - GET /api/inventory/inventory-items/ - Lista todos los artículos de inventario
    - POST /api/inventory/inventory-items/ - Crear nuevo artículo en inventario
    - GET /api/inventory/inventory-items/{id}/ - Detalle de artículo de inventario
    - PUT/PATCH /api/inventory/inventory-items/{id}/ - Actualizar artículo de inventario
    - DELETE /api/inventory/inventory-items/{id}/ - Eliminar artículo de inventario
    - POST /api/inventory/inventory-items/{id}/update-quantity/ - Actualizar cantidad
    - GET /api/inventory/inventory-items/low-stock/ - Todos los artículos con stock bajo
    """
    queryset = InventoryItem.objects.select_related('item', 'inventory', 'inventory__hostel').all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['inventory', 'item', 'is_active', 'item__category']
    search_fields = ['item__name', 'item__description', 'inventory__name', 'inventory__hostel__name']
    ordering_fields = ['created_at', 'quantity', 'item__name', 'item__category']
    ordering = ['item__category', 'item__name']

    def get_serializer_class(self):
        """Usar serializer diferente según la acción"""
        if self.action == 'retrieve':
            return InventoryItemDetailSerializer
        elif self.action == 'update_quantity':
            return InventoryItemQuantityUpdateSerializer
        return InventoryItemSerializer

    def perform_create(self, serializer):
        """Personalizar creación de artículo de inventario"""
        instance = serializer.save(created_by=self.request.user)
        return instance

    def perform_update(self, serializer):
        """Personalizar actualización de artículo de inventario"""
        instance = serializer.save(updated_by=self.request.user)
        return instance

    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        """
        Actualizar la cantidad de un artículo específico.
        
        POST /api/inventory/inventory-items/{id}/update-quantity/
        Body: {
            "action": "add|remove|set",
            "amount": 10
        }
        """
        inventory_item = self.get_object()
        serializer = InventoryItemQuantityUpdateSerializer(
            inventory_item,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_item = serializer.save()
            response_serializer = InventoryItemSerializer(updated_item)
            
            return Response({
                'message': 'Cantidad actualizada exitosamente',
                'item': response_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Lista todos los artículos con stock bajo en todos los inventarios.
        
        GET /api/inventory/inventory-items/low-stock/?threshold=5
        """
        threshold = int(request.query_params.get('threshold', 5))
        
        low_stock_items = self.get_queryset().filter(
            quantity__lte=threshold,
            is_active=True
        )
        
        # Aplicar filtros adicionales
        filtered_items = self.filter_queryset(low_stock_items)
        
        page = self.paginate_queryset(filtered_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'threshold': threshold,
                'results': serializer.data
            })

        serializer = self.get_serializer(filtered_items, many=True)
        return Response({
            'threshold': threshold,
            'count': filtered_items.count(),
            'results': serializer.data
        })
