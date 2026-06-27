import django_filters
from .models import AlertRecord


class AlertRecordFilter(django_filters.FilterSet):
    alert_name = django_filters.CharFilter(lookup_expr='icontains')
    project = django_filters.CharFilter(lookup_expr='icontains')
    host = django_filters.CharFilter(lookup_expr='icontains')
    ip_address = django_filters.CharFilter(lookup_expr='icontains')
    alert_level = django_filters.ChoiceFilter(choices=AlertRecord.AlertLevel.choices)
    current_status = django_filters.ChoiceFilter(choices=AlertRecord.CurrentStatus.choices)
    special_handle_type = django_filters.ChoiceFilter(choices=AlertRecord.HandleType.choices)
    trigger_time_after = django_filters.DateTimeFilter(field_name='trigger_time', lookup_expr='gte')
    trigger_time_before = django_filters.DateTimeFilter(field_name='trigger_time', lookup_expr='lte')
    registered_at_after = django_filters.DateTimeFilter(field_name='registered_at', lookup_expr='gte')
    registered_at_before = django_filters.DateTimeFilter(field_name='registered_at', lookup_expr='lte')
    is_permanent_mute = django_filters.BooleanFilter()
    
    class Meta:
        model = AlertRecord
        fields = [
            'alert_name', 'project', 'host', 'ip_address',
            'alert_level', 'current_status', 'special_handle_type',
            'is_permanent_mute'
        ]
