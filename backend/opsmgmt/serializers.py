from rest_framework import serializers
from .models import AlertRecord


class AlertRecordSerializer(serializers.ModelSerializer):
    alert_level_display = serializers.CharField(
        source='get_alert_level_display',
        read_only=True
    )
    current_status_display = serializers.CharField(
        source='get_current_status_display',
        read_only=True
    )
    special_handle_type_display = serializers.CharField(
        source='get_special_handle_type_display',
        read_only=True
    )
    
    class Meta:
        model = AlertRecord
        fields = '__all__'
        extra_kwargs = {
            'registered_at': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'duration': {'read_only': True},
        }
    
    def create(self, validated_data):
        # 自动填充登记人为当前用户
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['registered_by'] = request.user.username
        return super().create(validated_data)
