"""
URL configuration for caritas_backend project.
"""
from django.urls import path, include, re_path
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect
from django.conf import settings
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
import os

def documentation_view(request):
    """Vista principal de documentación"""
    html_content = '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API de Caritas - Documentación</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0; padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; display: flex; align-items: center; justify-content: center;
            }
            .container {
                background: white; border-radius: 20px; padding: 40px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center; max-width: 600px; width: 90%;
            }
            h1 { color: #333; margin-bottom: 20px; font-size: 2.5em; }
            .description { color: #666; margin-bottom: 30px; line-height: 1.6; }
            .buttons { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
            .btn {
                padding: 15px 30px; border: none; border-radius: 10px;
                text-decoration: none; font-weight: bold; font-size: 16px;
                transition: all 0.3s ease; cursor: pointer; display: inline-block;
            }
            .btn-primary { background: #667eea; color: white; }
            .btn-primary:hover { background: #5a6fd8; transform: translateY(-2px); }
            .btn-secondary { background: #764ba2; color: white; }
            .btn-secondary:hover { background: #6a4190; transform: translateY(-2px); }
            .btn-info { background: #17a2b8; color: white; }
            .btn-info:hover { background: #138496; transform: translateY(-2px); }
            .features {
                margin-top: 40px; text-align: left; background: #f8f9fa;
                padding: 20px; border-radius: 10px;
            }
            .features h3 { color: #333; margin-bottom: 15px; }
            .features ul { color: #666; line-height: 1.8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 API de Caritas</h1>
            <p class="description">
                Sistema de Gestión de Albergues - Documentación completa de la API REST
            </p>
            
            <div class="buttons">
                <a href="/swagger/" class="btn btn-primary">📖 Swagger UI</a>
                <a href="/redoc/" class="btn btn-secondary">📋 ReDoc</a>
                <a href="/api/schema/" class="btn btn-info">📄 API Schema</a>
            </div>
            
            <div class="features">
                <h3>🚀 Módulos de la API:</h3>
                <ul>
                    <li><strong>Usuarios:</strong> Pre-registros, administradores, autenticación</li>
                    <li><strong>Albergues:</strong> Ubicaciones, albergues, reservas de alojamiento</li>
                    <li><strong>Servicios:</strong> Servicios, horarios, reservas de servicios</li>
                    <li><strong>Inventario:</strong> Artículos, inventarios, control de stock</li>
                </ul>
            </div>
            
            <p style="margin-top: 30px; color: #999; font-size: 14px;">
                Desarrollado con ❤️ para la organización Caritas
            </p>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html_content, content_type='text/html')

def custom_schema_view(request):
    """Vista para servir el archivo YAML estático"""
    yaml_path = os.path.join(settings.BASE_DIR, 'swagger_documentation.yaml')
    if os.path.exists(yaml_path):
        return FileResponse(
            open(yaml_path, 'rb'),
            content_type='application/x-yaml',
            filename='swagger_documentation.yaml'
        )
    else:
        return HttpResponse("Archivo de esquema no encontrado", status=404)

urlpatterns = [    
    # Endpoint principal de documentación
    path('', documentation_view, name='documentation'),
    path('api/documentation/', documentation_view, name='api-documentation'),
    
    # API REST
    path('api/users/', include('users.urls')),
    path('api/albergues/', include('albergues.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/services/', include('services.urls')),
    
    # Swagger UI - usando el archivo YAML estático
    path('api/schema/', custom_schema_view, name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
