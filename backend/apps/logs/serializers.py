from rest_framework import serializers
from apps.logs.models import OperationLog, LoginLog

class LoginLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginLog
        fields = '__all__'

class OperationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='未知')

    class Meta:
        model = OperationLog
        fields = '__all__'