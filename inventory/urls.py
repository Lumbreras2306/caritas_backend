# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ItemViewSet,
    InventoryViewSet,
    InventoryItemViewSet
)

# ============================================================================
# CONFIGURACIÓN DE ROUTERS
# ============================================================================

# Router principal para ViewSets de inventario
router = DefaultRouter()

# Registrar ViewSets en el router
router.register(r'items', ItemViewSet, basename='item')
router.register(r'inventories', InventoryViewSet, basename='inventory')
router.register(r'inventory-items', InventoryItemViewSet, basename='inventoryitem')

# ============================================================================
# PATRONES DE URL
# ============================================================================

urlpatterns = [
    # URLs generadas automáticamente por el router
    path('', include(router.urls)),
]

# ============================================================================
# DOCUMENTACIÓN DE ENDPOINTS DISPONIBLES
# ============================================================================

"""
ENDPOINTS GENERADOS AUTOMÁTICAMENTE POR EL ROUTER:

Artículos:
- GET    /api/inventory/items/                        - Lista todos los artículos
- POST   /api/inventory/items/                        - Crear nuevo artículo
- GET    /api/inventory/items/{id}/                   - Detalle de artículo
- PUT    /api/inventory/items/{id}/                   - Actualizar artículo completo
- PATCH  /api/inventory/items/{id}/                   - Actualizar artículo parcial
- DELETE /api/inventory/items/{id}/                   - Eliminar artículo
- GET    /api/inventory/items/categories/             - Lista de categorías únicas
- GET    /api/inventory/items/units/                  - Lista de unidades únicas

Inventarios:
- GET    /api/inventory/inventories/                  - Lista todos los inventarios
- POST   /api/inventory/inventories/                  - Crear nuevo inventario
- GET    /api/inventory/inventories/{id}/             - Detalle de inventario
- PUT    /api/inventory/inventories/{id}/             - Actualizar inventario completo
- PATCH  /api/inventory/inventories/{id}/             - Actualizar inventario parcial
- DELETE /api/inventory/inventories/{id}/             - Eliminar inventario
- GET    /api/inventory/inventories/{id}/summary/     - Resumen del inventario

Artículos de Inventario:
- GET    /api/inventory/inventory-items/              - Lista todos los artículos de inventario
- POST   /api/inventory/inventory-items/              - Crear nuevo artículo en inventario
- GET    /api/inventory/inventory-items/{id}/         - Detalle de artículo de inventario
- PUT    /api/inventory/inventory-items/{id}/         - Actualizar artículo completo
- PATCH  /api/inventory/inventory-items/{id}/         - Actualizar artículo parcial
- DELETE /api/inventory/inventory-items/{id}/         - Eliminar artículo de inventario
- POST   /api/inventory/inventory-items/{id}/update-quantity/ - Actualizar cantidad
- GET    /api/inventory/inventory-items/low-stock/    - Artículos con stock bajo

FILTROS Y BÚSQUEDAS DISPONIBLES:

Artículos:
- Filtros: ?category=Higiene&unit=piezas&is_active=true
- Búsqueda: ?search=Jabón (busca en nombre, descripción, categoría)
- Ordenamiento: ?ordering=category,name

Inventarios:
- Filtros: ?hostel={uuid}&is_active=true
- Búsqueda: ?search=Principal (busca en nombre, descripción, nombre del albergue)
- Ordenamiento: ?ordering=-last_updated

Artículos de Inventario:
- Filtros: ?inventory={uuid}&item__category=Alimentos&is_active=true
- Búsqueda: ?search=Arroz (busca en nombre del artículo, descripción, nombre del inventario)
- Ordenamiento: ?ordering=item__category,item__name

EJEMPLOS DE USO:

1. Crear artículo:
POST /api/inventory/items/
{
    "name": "Jabón antibacterial",
    "description": "Jabón líquido antibacterial 500ml",
    "category": "Higiene",
    "unit": "botellas"
}

2. Crear inventario:
POST /api/inventory/inventories/
{
    "hostel": "{hostel_uuid}",
    "name": "Inventario Principal",
    "description": "Inventario principal del albergue"
}

3. Agregar artículo a inventario:
POST /api/inventory/inventory-items/
{
    "inventory": "{inventory_uuid}",
    "item": "{item_uuid}",
    "quantity": 50,
    "minimum_stock": 10
}

4. Actualizar cantidad de artículo:
POST /api/inventory/inventory-items/{id}/update-quantity/
{
    "action": "add",
    "amount": 20
}

5. Consultar resumen de inventario:
GET /api/inventory/inventories/{id}/summary/

6. Ver artículos con stock bajo:
GET /api/inventory/inventory-items/low-stock/?threshold=5

7. Filtrar por categoría:
GET /api/inventory/inventory-items/?item__category=Alimentos&ordering=quantity
"""
