from django.contrib import admin
from .models import AlertRecord


@admin.register(AlertRecord)
class AlertRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'alert_name', 'project', 'host', 'ip_address',
        'alert_level', 'current_status', 'trigger_time', 'registered_at'
    ]
    list_filter = ['alert_level', 'current_status', 'special_handle_type', 'is_permanent_mute']
    search_fields = ['alert_name', 'project', 'host', 'ip_address', 'mute_reason']
    ordering = ['-registered_at']
    readonly_fields = ['registered_at', 'created_at', 'updated_at', 'duration']
