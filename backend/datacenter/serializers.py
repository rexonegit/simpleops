from rest_framework import serializers

from .models import VMwareVM, ProjectVMware, ProjectNetworkDevice, ProjectBareMetal, ProjectProxmox, ProxmoxVM


class VMwareVMSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tools_status_display = serializers.CharField(source='get_tools_status_display', read_only=True)
    tools_running_status_display = serializers.CharField(source='get_tools_running_status_display', read_only=True)
    memory_gb = serializers.FloatField(read_only=True)
    storage_available = serializers.FloatField(read_only=True)
    formatted_uptime = serializers.CharField(read_only=True)

    class Meta:
        model = VMwareVM
        fields = '__all__'

class ProjectVMwareSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )

    class Meta:
        model = ProjectVMware
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class ProjectBareMetalSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectBareMetal
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class ProjectNetworkDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectNetworkDevice
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class ProjectProxmoxSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )

    class Meta:
        model = ProjectProxmox
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def validate_vmid(self, value):
        """验证VMID唯一性"""
        if not value:
            return value
        
        # 获取当前实例（编辑时）
        instance = getattr(self, 'instance', None)
        
        # 查询是否存在相同VMID
        queryset = ProjectProxmox.objects.filter(vmid=value)
        if instance:
            # 编辑时，排除自身
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            existing = queryset.first()
            raise serializers.ValidationError(
                f'VMID "{value}" 已被主机 "{existing.hostname}" 使用，请使用其他VMID'
            )
        return value


class ProxmoxVMSerializer(serializers.ModelSerializer):
    """Proxmox虚拟机资产序列化器"""
    status_display = serializers.CharField(source='get_status_display_cn', read_only=True)
    ha_state_display = serializers.CharField(source='get_ha_state_display_cn', read_only=True)
    memory_gb = serializers.FloatField(read_only=True)
    formatted_uptime = serializers.CharField(read_only=True)
    is_backup_healthy = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProxmoxVM
        fields = '__all__'
        extra_kwargs = {
            'last_sync': {'read_only': True},
            'created_at': {'read_only': True},
        }

