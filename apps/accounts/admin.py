from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'name', 'is_active', 'failed_login_attempts', 'last_login']
    list_filter = ['is_active', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'name']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('name', 'failed_login_attempts', 'locked_until')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('name', 'email')}),
    )
