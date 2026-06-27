#过滤文件，可指定搜索字段
import django_filters
from django.db.models import Q
from .models import AliyunECS, AliyunDNSRecord
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)

class AliyunECSFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='custom_search', label="Any_field")
    project = django_filters.CharFilter(field_name='project', lookup_expr='icontains')
    owner = django_filters.CharFilter(field_name='owner', lookup_expr='icontains')

    class Meta:
        model = AliyunECS
        fields = {
            'hostname': ['exact', 'icontains'],
            'owner': ['exact', 'icontains'],
            'project': ['exact', 'icontains'],
            'private_ip': ['exact', 'icontains'],
            'status': ['exact'],
            'environment': ['exact'],
        }

    def custom_search(self, queryset, name, value):
        try:
            # 记录搜索值
            logger.info(f"Searching for value: {value}")

            # 使用 Q 对象来构建复杂的查询条件
            filtered_queryset = queryset.filter(
                Q(hostname__icontains=value) |
                Q(owner__icontains=value) |
                Q(project__icontains=value) |
                Q(private_ip__icontains=value) |
                Q(public_ip__icontains=value) |
                Q(account_name__icontains=value)
            )

            # 记录过滤后的查询集数量
            logger.info(f"Filtered queryset count: {filtered_queryset.count()}")

            return filtered_queryset
        except Exception as e:
            logger.error(f"Error during custom search: {str(e)}")
            return queryset  # 返回原始查询集或空查询集，根据需求选择


class AliyunDNSRecordFilter(django_filters.FilterSet):
    class Meta:
        model = AliyunDNSRecord
        fields = {
            'domain_name': ['exact', 'icontains'],
            'owner': ['exact', 'icontains'],
            'project': ['exact', 'icontains'],
            'complete_domain': ['exact', 'icontains'],
        }