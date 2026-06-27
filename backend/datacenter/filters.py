import django_filters
from .models import VMwareVM, ProxmoxVM
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


class VMwareVMFilter(django_filters.FilterSet):
    class Meta:
        model = VMwareVM
        fields = {
            'name': ['exact', 'icontains'],
            'owner': ['exact', 'icontains'],
            'project_name': ['exact', 'icontains'],
            'ip_address': ['exact', 'icontains'],
            'status': ['exact'],
            'environment_type': ['exact'],
            'vcenter_host': ['exact', 'icontains'],
            'tools_status': ['exact'],
            'tools_running_status': ['exact'],
        }


    def filter_backup_status(self, queryset, name, value):
        if value == 'healthy':
            return queryset.filter(is_backup_healthy=True)
        elif value == 'unhealthy':
            return queryset.filter(is_backup_healthy=False)
        elif value == 'no_backup':
            return queryset.filter(backup_policy__isnull=True)
        return queryset

    def search_filter(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            django_filters.Q(hostname__icontains=value) |
            django_filters.Q(project_name__icontains=value) |
            django_filters.Q(owner__icontains=value) |
            django_filters.Q(ip_address__icontains=value)
        )


class ProxmoxVMFilter(django_filters.FilterSet):
    """Proxmox虚拟机过滤器"""
    has_backup = django_filters.BooleanFilter(method='filter_has_backup')
    ha_enabled = django_filters.BooleanFilter(method='filter_ha_enabled')

    # 添加备份状态筛选（使用CharFilter支持字符串参数）
    backup_status = django_filters.CharFilter(method='filter_backup_status')

    class Meta:
        model = ProxmoxVM
        fields = {
            'vmid': ['exact', 'icontains'],
            'name': ['exact', 'icontains'],
            'node': ['exact'],
            'cluster': ['exact', 'icontains'],
            'status': ['exact'],
            'environment_type': ['exact'],
            'ha_state': ['exact'],
            'project_name': ['exact', 'icontains'],
            'owner': ['exact', 'icontains'],
            'storage': ['exact'],
            'template': ['exact'],
            'agent_enabled': ['exact'],
            # 添加 last_backup 支持 isnull 查找
            'last_backup': ['isnull'],
        }

    def filter_has_backup(self, queryset, name, value):
        """过滤是否有备份"""
        if value:
            return queryset.filter(last_backup__isnull=False)
        return queryset.filter(last_backup__isnull=True)

    def filter_ha_enabled(self, queryset, name, value):
        """过滤是否启用高可用"""
        if value:
            return queryset.exclude(ha_state='').exclude(ha_state__isnull=True)
        return queryset.filter(models.Q(ha_state='') | models.Q(ha_state__isnull=True))

    def filter_backup_status(self, queryset, name, value):
        """自定义备份状态筛选（支持 backed_up / no_backup）"""
        if value == 'backed_up':
            return queryset.filter(last_backup__isnull=False)
        elif value == 'no_backup':
            return queryset.filter(last_backup__isnull=True)
        return queryset