from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from .models import AlertRecord
from .serializers import AlertRecordSerializer
from .filters import AlertRecordFilter
from apps.utils.pagination import CustomPagination


class AlertRecordViewSet(viewsets.ModelViewSet):
    """告警记录 ViewSet"""
    queryset = AlertRecord.objects.all()
    serializer_class = AlertRecordSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlertRecordFilter
    search_fields = ['alert_name', 'project', 'host', 'ip_address', 'monitor_item', 'mute_reason']
    ordering_fields = [
        'registered_at', 'trigger_time', 'recovery_time',
        'alert_level', 'current_status', 'project', 'host'
    ]
    ordering = ['-registered_at']
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取告警统计信息"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # 总数
        total = queryset.count()
        
        # 按状态统计
        status_stats = queryset.values('current_status').annotate(
            count=Count('id')
        ).order_by('current_status')
        status_counts = {item['current_status']: item['count'] for item in status_stats}
        
        # 按级别统计
        level_stats = queryset.values('alert_level').annotate(
            count=Count('id')
        ).order_by('alert_level')
        level_counts = {item['alert_level']: item['count'] for item in level_stats}
        
        # 按项目统计
        project_stats = queryset.values('project').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'total': total,
            'status_counts': status_counts,
            'level_counts': level_counts,
            'project_stats': list(project_stats)
        })
