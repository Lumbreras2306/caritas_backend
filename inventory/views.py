# views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg

# DRF Spectacular imports para documentación automática
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Item, Inventory, InventoryItem
from .serializers import (
    ItemSerializer, InventorySerializer, InventoryItemSerializer,
    InventoryItemQuantityUpdateSerializer, InventoryItemDetailSerializer
)

# ============================================================================
# VIEWSETS PARA ARTÍCULOS
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Inventario'],
        summary="Lista artículos",
        description="Obtiene lista paginada de artículos del sistema de inventario",
        parameters=[
            OpenApiParameter(name='category', type=OpenApiTypes.STR, description='Filtrar por categoría'),
            OpenApiParameter(name='unit', type=OpenApiTypes.STR, description='Filtrar por unidad de medida'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Filtrar por estado activo'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre, descripción, categoría'),
        ]
    ),
    create=extend_schema(
        tags=['Inventario'],
        summary="Crear artículo",
        description="Crea un nuevo artículo para usar en inventarios",
        examples=[
            OpenApiExample(
                'Artículo de higiene',
                value={
                    "name": "Jabón antibacterial",
                    "description": "Jabón líquido antibacterial 500ml",
                    "category": "Higiene",
                    "unit": "botellas"
                }
            ),
            OpenApiExample(
                'Artículo de alimentos',
                value={
                    "name": "Arroz blanco",
                    "description": "Arroz blanco de grano largo",
                    "category": "Alimentos",
                    "unit": "kilogramos"
                }
            ),
            OpenApiExample(
                'Artículo de limpieza',
                value={
                    "name": "Detergente en polvo",
                    "description": "Detergente para lavado de ropa",
                    "category": "Limpieza",
                    "unit": "cajas"
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Inventario'], summary="Detalle de artículo"),
    update=extend_schema(tags=['Inventario'], summary="Actualizar artículo"),
    partial_update=extend_schema(tags=['Inventario'], summary="Actualizar artículo parcial"),
    destroy=extend_schema(tags=['Inventario'], summary="Eliminar artículo"),
)
class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de artículos.
    
    Los artículos son productos o elementos que pueden ser almacenados
    en los inventarios de los albergues (comida, ropa, medicinas, etc.).
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

    @extend_schema(
        tags=['Inventario'],
        summary="Lista categorías únicas",
        description="Obtiene una lista de todas las categorías únicas de artículos",
        responses={
            200: OpenApiResponse(description="Categorías obtenidas exitosamente"),
        }
    )
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Lista todas las categorías únicas de artículos."""
        categories = Item.objects.values_list('category', flat=True).distinct().order_by('category')
        return Response({
            'categories': list(categories),
            'count': len(categories)
        })

    @extend_schema(
        tags=['Inventario'],
        summary="Lista unidades únicas",
        description="Obtiene una lista de todas las unidades de medida únicas",
        responses={
            200: OpenApiResponse(description="Unidades obtenidas exitosamente"),
        }
    )
    @action(detail=False, methods=['get'])
    def units(self, request):
        """Lista todas las unidades de medida únicas."""
        units = Item.objects.values_list('unit', flat=True).distinct().order_by('unit')
        return Response({
            'units': list(units),
            'count': len(units)
        })

# ============================================================================
# VIEWSETS PARA INVENTARIOS
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Inventario'],
        summary="Lista inventarios",
        description="Obtiene lista paginada de inventarios por albergue",
        parameters=[
            OpenApiParameter(name='hostel', type=OpenApiTypes.UUID, description='Filtrar por albergue'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Filtrar por estado activo'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre, descripción, nombre del albergue'),
        ]
    ),
    create=extend_schema(
        tags=['Inventario'],
        summary="Crear inventario",
        description="Crea un nuevo inventario para un albergue",
        examples=[
            OpenApiExample(
                'Inventario principal',
                value={
                    "hostel": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Inventario Principal",
                    "description": "Inventario principal del albergue Casa San José"
                }
            ),
            OpenApiExample(
                'Inventario de emergencia',
                value={
                    "hostel": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "Inventario de Emergencia",
                    "description": "Inventario para situaciones de emergencia"
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Inventario'], summary="Detalle de inventario"),
    update=extend_schema(tags=['Inventario'], summary="Actualizar inventario"),
    partial_update=extend_schema(tags=['Inventario'], summary="Actualizar inventario parcial"),
    destroy=extend_schema(tags=['Inventario'], summary="Eliminar inventario"),
)
class InventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de inventarios.
    
    Los inventarios organizan y controlan los artículos disponibles
    en cada albergue, permitiendo un seguimiento detallado del stock.
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

    @extend_schema(
        tags=['Inventario'],
        summary="Resumen del inventario",
        description="Obtiene resumen completo del inventario con estadísticas y análisis por categoría",
        responses={
            200: OpenApiResponse(description="Resumen obtenido exitosamente"),
            404: OpenApiResponse(description="Inventario no encontrado"),
        }
    )
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Resumen completo del inventario."""
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
            avg_quantity=Avg('quantity'),
            min_quantity=Sum('quantity'),
            low_stock_count=Count('id', filter=Q(quantity__lte=F('minimum_stock')))
        ).order_by('item__category')
        
        # Top 10 artículos con más stock
        top_stock_items = inventory.inventory_items.filter(
            is_active=True
        ).select_related('item').order_by('-quantity')[:10]
        
        return Response({
            'inventory': {
                'id': inventory.id,
                'name': inventory.name,
                'hostel': inventory.hostel.name,
                'hostel_location': inventory.hostel.get_formatted_address(),
                'last_updated': inventory.last_updated
            },
            'summary': {
                'total_different_items': total_items,
                'total_quantity_all_items': total_quantity,
                'low_stock_count': low_stock_items.count(),
                'empty_stock_count': empty_stock_items.count(),
                'categories_count': items_by_category.count()
            },
            'by_category': list(items_by_category),
            'top_stock_items': [
                {
                    'item_name': item.item.name,
                    'category': item.item.category,
                    'quantity': item.quantity,
                    'unit': item.item.unit
                }
                for item in top_stock_items
            ],
            'alerts': {
                'low_stock_items': [
                    {
                        'item_name': item.item.name,
                        'current_quantity': item.quantity,
                        'minimum_stock': item.minimum_stock
                    }
                    for item in low_stock_items
                ]
            }
        })

# ============================================================================
# VIEWSETS PARA ARTÍCULOS DE INVENTARIO
# ============================================================================

@extend_schema_view(
    list=extend_schema(
        tags=['Inventario'],
        summary="Lista artículos en inventarios",
        description="Obtiene lista de artículos con su stock en inventarios específicos",
        parameters=[
            OpenApiParameter(name='inventory', type=OpenApiTypes.UUID, description='Filtrar por inventario'),
            OpenApiParameter(name='item', type=OpenApiTypes.UUID, description='Filtrar por artículo'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Filtrar por estado activo'),
            OpenApiParameter(name='item__category', type=OpenApiTypes.STR, description='Filtrar por categoría de artículo'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Busca en nombre del artículo, descripción, inventario'),
        ]
    ),
    create=extend_schema(
        tags=['Inventario'],
        summary="Agregar artículo a inventario",
        description="Agrega un artículo específico a un inventario con cantidad inicial",
        examples=[
            OpenApiExample(
                'Agregar jabón al inventario',
                value={
                    "inventory": "123e4567-e89b-12d3-a456-426614174000",
                    "item": "123e4567-e89b-12d3-a456-426614174001",
                    "quantity": 50,
                    "minimum_stock": 10
                }
            ),
            OpenApiExample(
                'Agregar arroz al inventario',
                value={
                    "inventory": "123e4567-e89b-12d3-a456-426614174000",
                    "item": "123e4567-e89b-12d3-a456-426614174002",
                    "quantity": 100,
                    "minimum_stock": 20
                }
            )
        ]
    ),
    retrieve=extend_schema(tags=['Inventario'], summary="Detalle de artículo en inventario"),
    update=extend_schema(tags=['Inventario'], summary="Actualizar artículo en inventario"),
    partial_update=extend_schema(tags=['Inventario'], summary="Actualizar artículo parcial"),
    destroy=extend_schema(tags=['Inventario'], summary="Eliminar artículo de inventario"),
)
class InventoryItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de artículos en inventarios.
    
    Permite gestionar el stock de artículos específicos en inventarios,
    incluyendo cantidades, stock mínimo y operaciones de actualización.
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

    @extend_schema(
        tags=['Inventario'],
        summary="Actualizar cantidad",
        description="Actualiza la cantidad de un artículo específico en inventario usando operaciones (set, add, remove)",
        request=InventoryItemQuantityUpdateSerializer,
        responses={
            200: OpenApiResponse(description="Cantidad actualizada exitosamente"),
            400: OpenApiResponse(description="Datos inválidos o operación no válida"),
            404: OpenApiResponse(description="Artículo de inventario no encontrado"),
        },
        examples=[
            OpenApiExample(
                'Establecer cantidad exacta',
                value={
                    "action": "set",
                    "amount": 100
                },
                description='Establece la cantidad exacta en 100 unidades'
            ),
            OpenApiExample(
                'Agregar stock',
                value={
                    "action": "add",
                    "amount": 25
                },
                description='Agrega 25 unidades al stock actual'
            ),
            OpenApiExample(
                'Quitar stock',
                value={
                    "action": "remove",
                    "amount": 10
                },
                description='Quita 10 unidades del stock actual'
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        """Actualizar la cantidad de un artículo específico."""
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
                'action': request.data.get('action'),
                'amount': request.data.get('amount'),
                'previous_quantity': inventory_item.quantity,
                'new_quantity': updated_item.quantity,
                'item': response_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Inventario'],
        summary="Artículos con stock bajo",
        description="Lista todos los artículos con stock por debajo del umbral especificado",
        parameters=[
            OpenApiParameter(name='threshold', type=OpenApiTypes.INT, description='Umbral de stock bajo (default: 5)'),
            OpenApiParameter(name='inventory', type=OpenApiTypes.UUID, description='Filtrar por inventario específico'),
        ],
        responses={
            200: OpenApiResponse(description="Artículos con stock bajo obtenidos exitosamente"),
        }
    )
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Lista todos los artículos con stock bajo en todos los inventarios."""
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
                'message': f'Artículos con stock igual o menor a {threshold}',
                'results': serializer.data
            })

        serializer = self.get_serializer(filtered_items, many=True)
        return Response({
            'threshold': threshold,
            'count': filtered_items.count(),
            'message': f'Artículos con stock igual o menor a {threshold}',
            'results': serializer.data
        })

    @extend_schema(
        tags=['Inventario'],
        summary="Artículos sin stock",
        description="Lista todos los artículos que están sin stock (cantidad = 0)",
        parameters=[
            OpenApiParameter(name='inventory', type=OpenApiTypes.UUID, description='Filtrar por inventario específico'),
        ],
        responses={
            200: OpenApiResponse(description="Artículos sin stock obtenidos exitosamente"),
        }
    )
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Lista todos los artículos sin stock."""
        out_of_stock_items = self.get_queryset().filter(
            quantity=0,
            is_active=True
        )
        
        # Aplicar filtros adicionales
        filtered_items = self.filter_queryset(out_of_stock_items)
        
        page = self.paginate_queryset(filtered_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'message': 'Artículos sin stock disponible',
                'results': serializer.data
            })

        serializer = self.get_serializer(filtered_items, many=True)
        return Response({
            'count': filtered_items.count(),
            'message': 'Artículos sin stock disponible',
            'results': serializer.data
        })
