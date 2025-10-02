// swagger_auth.js
// Script personalizado para mejorar la experiencia de autenticación en Swagger UI

(function() {
    'use strict';
    
    // Función para mostrar notificación
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 14px;
            max-width: 400px;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    // Función para obtener token del login
    function handleLoginResponse(response) {
        try {
            const data = JSON.parse(response);
            if (data.token) {
                // Guardar token en localStorage
                localStorage.setItem('swagger-ui-token', data.token);
                
                // Actualizar el campo de autorización
                const authInput = document.querySelector('input[placeholder*="Authorization"]');
                if (authInput) {
                    authInput.value = `Token ${data.token}`;
                }
                
                showNotification('✅ Token obtenido exitosamente. Ya puedes usar los endpoints protegidos.', 'success');
                
                // Cerrar el modal de autorización si está abierto
                const closeBtn = document.querySelector('.auth-btn-wrapper .authorize');
                if (closeBtn) {
                    closeBtn.click();
                }
            } else {
                showNotification('❌ Error: No se recibió token en la respuesta', 'error');
            }
        } catch (e) {
            showNotification('❌ Error al procesar la respuesta del login', 'error');
        }
    }
    
    // Función para crear botón de login rápido
    function createQuickLoginButton() {
        const authWrapper = document.querySelector('.auth-btn-wrapper');
        if (!authWrapper || document.querySelector('#quick-login-btn')) return;
        
        const quickLoginBtn = document.createElement('button');
        quickLoginBtn.id = 'quick-login-btn';
        quickLoginBtn.innerHTML = '🔑 Login Rápido';
        quickLoginBtn.style.cssText = `
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
            font-size: 14px;
            font-weight: bold;
        `;
        
        quickLoginBtn.onclick = function() {
            const username = prompt('Usuario administrador:');
            const password = prompt('Contraseña:', '');
            
            if (username && password) {
                fetch('/api/users/auth/admin-login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                })
                .then(response => response.text())
                .then(data => handleLoginResponse(data))
                .catch(error => {
                    showNotification('❌ Error de conexión: ' + error.message, 'error');
                });
            }
        };
        
        authWrapper.appendChild(quickLoginBtn);
    }
    
    // Función para agregar información de autenticación
    function addAuthInfo() {
        const topbar = document.querySelector('.topbar');
        if (!topbar || document.querySelector('#auth-info')) return;
        
        const authInfo = document.createElement('div');
        authInfo.id = 'auth-info';
        authInfo.innerHTML = `
            <div style="
                background: #e3f2fd;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
                font-size: 14px;
                color: #1976d2;
            ">
                <strong>🔐 Autenticación:</strong> Usa el botón "Authorize" para configurar tu token de administrador, 
                o usa el botón "Login Rápido" para autenticarte directamente.
            </div>
        `;
        
        topbar.appendChild(authInfo);
    }
    
    // Función para interceptar requests y agregar token automáticamente
    function setupRequestInterceptor() {
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            const token = localStorage.getItem('swagger-ui-token');
            if (token && !options.headers) {
                options.headers = {};
            }
            if (token && options.headers) {
                options.headers['Authorization'] = `Token ${token}`;
            }
            return originalFetch.call(this, url, options);
        };
    }
    
    // Inicializar cuando el DOM esté listo
    function init() {
        // Esperar a que Swagger UI esté completamente cargado
        const checkSwagger = setInterval(() => {
            if (document.querySelector('.swagger-ui') && document.querySelector('.auth-btn-wrapper')) {
                clearInterval(checkSwagger);
                
                createQuickLoginButton();
                addAuthInfo();
                setupRequestInterceptor();
                
                // Mostrar mensaje de bienvenida
                setTimeout(() => {
                    showNotification('🚀 Swagger UI cargado. Usa "Authorize" o "Login Rápido" para autenticarte.', 'info');
                }, 1000);
            }
        }, 100);
    }
    
    // Inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
