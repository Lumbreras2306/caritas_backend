from django.contrib import admin
from .models import (
    AdminUser, PreRegisterUser, CustomUser, CustomUserToken,
    STATUS_CHOICES, GENDER_CHOICES, POVERTY_LEVEL_CHOICES
)

# ============================================================================
# ADMINISTRACIÓN DE USUARIOS ADMINISTRADORES
# ============================================================================

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'is_active', 'is_staff', 'is_superuser', 'last_login']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['username', 'first_name', 'last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']

# ============================================================================
# ADMINISTRACIÓN DE PRE-REGISTROS
# ============================================================================

@admin.register(PreRegisterUser)
class PreRegisterUserAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'phone_number', 'age', 'gender', 'status', 'created_at']
    list_filter = ['status', 'gender', 'privacy_policy_accepted', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at']

# ============================================================================
# ADMINISTRACIÓN DE USUARIOS FINALES
# ============================================================================

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'phone_number', 'age', 'gender', 'poverty_level', 'is_active', 'approved_at']
    list_filter = ['is_active', 'gender', 'poverty_level', 'approved_at', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at', 'approved_at']

# ============================================================================
# ADMINISTRACIÓN DE TOKENS
# ============================================================================

@admin.register(CustomUserToken)
class CustomUserTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'key', 'created']
    list_filter = ['created']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone_number', 'key']
    readonly_fields = ['key', 'created']
