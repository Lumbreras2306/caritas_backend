"""
URL configuration for caritas_backend project.
"""
from django.urls import path, include
from django.http import HttpResponse
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

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
                text-align: center; max-width: 700px; width: 90%;
            }
            h1 { color: #333; margin-bottom: 20px; font-size: 2.5em; }
            .description { color: #666; margin-bottom: 30px; line-height: 1.6; }
            .buttons { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin-bottom: 30px; }
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
                padding: 25px; border-radius: 10px;
            }
            .features h3 { color: #333; margin-bottom: 15px; }
            .features ul { color: #666; line-height: 1.8; margin: 0; }
            .stats {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 20px; margin-top: 30px;
            }
            .stat-card {
                background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;
            }
            .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
            .stat-label { font-size: 0.9em; color: #666; }
            .auth-info {
                background: #e3f2fd; border: 1px solid #2196F3; border-radius: 8px;
                padding: 20px; margin: 20px 0; text-align: left;
            }
            .auth-info h4 { color: #1976d2; margin-top: 0; }
            .auth-info code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 API de Caritas</h1>
            <p class="description">
                Sistema de Gestión de Albergues - Documentación automática generada desde el código
            </p>
            
            <div class="auth-info">
                <h4>🔐 Autenticación</h4>
                <p><strong>Para usar los endpoints protegidos:</strong></p>
                <ol>
                    <li>Ve a <strong>Swagger UI</strong> y haz clic en el botón <strong>"Authorize"</strong></li>
                    <li>Obtén tu token usando: <code>POST /api/users/auth/admin-login/</code></li>
                    <li>Ingresa el token en el formato: <code>Token tu_token_aqui</code></li>
                    <li>¡Listo! Ya puedes usar todos los endpoints protegidos</li>
                </ol>
            </div>
            
            <div class="buttons">
                <a href="/swagger-auth/" class="btn btn-primary">📖 Swagger UI (Con Auth)</a>
                <a href="/swagger/" class="btn btn-secondary">📖 Swagger UI (Básico)</a>
                <a href="/redoc/" class="btn btn-secondary">📋 ReDoc</a>
                <a href="/api/schema/" class="btn btn-info">📄 API Schema</a>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">4</div>
                    <div class="stat-label">Módulos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">80+</div>
                    <div class="stat-label">Endpoints</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">100%</div>
                    <div class="stat-label">Automático</div>
                </div>
            </div>
            
            <div class="features">
                <h3>🚀 Módulos de la API:</h3>
                <ul>
                    <li><strong>Usuarios:</strong> Pre-registros, administradores, autenticación con Twilio</li>
                    <li><strong>Albergues:</strong> Ubicaciones, albergues, reservas de alojamiento</li>
                    <li><strong>Servicios:</strong> Servicios, horarios, reservas de servicios</li>
                    <li><strong>Inventario:</strong> Artículos, inventarios, control de stock</li>
                </ul>
                
                <h3>✨ Características:</h3>
                <ul>
                    <li><strong>Documentación automática:</strong> Siempre actualizada con el código</li>
                    <li><strong>Autenticación con tokens:</strong> Sistema seguro para administradores</li>
                    <li><strong>SMS con Twilio:</strong> Verificación de teléfonos</li>
                    <li><strong>API REST completa:</strong> CRUD, filtros, búsqueda, paginación</li>
                </ul>
            </div>
            
            <p style="margin-top: 30px; color: #999; font-size: 14px;">
                Desarrollado con ❤️ para la organización Caritas<br>
                <strong>Documentación generada automáticamente por DRF Spectacular</strong>
            </p>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html_content, content_type='text/html')

urlpatterns = [    
    # Panel de administración de Django
    path('admin/', admin.site.urls),
    
    # Endpoint principal de documentación
    path('', documentation_view, name='documentation'),
    path('api/documentation/', documentation_view, name='api-documentation'),
    
    # API REST
    path('api/users/', include('users.urls')),
    path('api/albergues/', include('albergues.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/services/', include('services.urls')),
    
    # Documentación automática con DRF Spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Swagger con autenticación mejorada
    path('swagger-auth/', TemplateView.as_view(
        template_name='swagger_auth.html',
        extra_context={'title': 'API de Caritas - Swagger UI'}
    ), name='swagger-auth'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
