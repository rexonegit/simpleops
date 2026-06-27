from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'phone', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('is_superuser', 'is_active')
    search_fields = ('username', 'phone')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('phone', 'avatar')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'roles')}),
    )
    filter_horizontal = ('roles',)