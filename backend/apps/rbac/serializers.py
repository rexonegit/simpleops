from rest_framework import serializers
from apps.rbac.models import Router, Role, Permission


class RouterTreeSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='title')

    class Meta:
        model = Router
        fields = ['id', 'label', 'type', 'parent']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'router']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'permissions']