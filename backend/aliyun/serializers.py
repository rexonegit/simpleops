# aliyun/serializers.py

import json

from rest_framework import serializers
from aliyun.models import (
    AliyunOSS, AliyunRAMUser, AliyunECS, ProjectAliyunecs, AliyunDomain, AliyunDNSRecord, ProjectAliyunDomain,
    AliyunSecurityGroup, AliyunSecurityGroupRule, AliyunSLB, ProjectAliyunSLB, AliyunRDS, ProjectAliyunRDS, AliyunEIP, AliyunWAF, AliyunWAF, AliyunNAS, ProjectAliyunNAS,
    AliyunSNATEntry, AliyunSLSLogStore, AliyunSLSProject, ProjectAliyunSLS
)
from apps.utils.response import ApiResponse



# ---------- 基础工具 ----------
def format_size(size_bytes):
    if not size_bytes:
        return '0 B'

    units = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
    i, size = 0, int(size_bytes)

    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0  # 使用浮点数除法
        i += 1

    # 根据单位决定显示的小数位数
    if i == 0:  # 字节单位，不需要小数
        return f'{size} {units[i]}'
    else:  # 其他单位，保留两位小数
        return f'{size:.2f} {units[i]}'


# ---------- 阿里云 OSS ----------
class AliyunOSSSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = AliyunOSS
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for k in ('storage', 'standard_storage', 'ia_storage', 'archive_storage',
                  'cold_archive_storage', 'deep_cold_archive_storage', 'monthly_flow'):
            data[k] = format_size(getattr(instance, k, 0))
        return data

class OSSBucketDetailSerializer(serializers.ModelSerializer):
    policy_info = serializers.SerializerMethodField()

    class Meta:
        model = AliyunOSS
        fields = '__all__'

    def get_policy_info(self, obj):
        try:
            if obj.tags and 'policy' in obj.tags:
                policy_data = obj.tags['policy']
                policy_content = policy_data.get('policy_content')

                if policy_content:
                    policy = json.loads(policy_content)
                    principals_info = []

                    for statement in policy.get('Statement', []):
                        principals = self.extract_principals(statement.get('Principal', {}))
                        actions = statement.get('Action', [])
                        resources = statement.get('Resource', [])
                        effect = statement.get('Effect', '')
                        conditions = statement.get('Condition', {})

                        # 将条件转换为列表格式
                        condition_list = []
                        if conditions:
                            for key, value in conditions.items():
                                condition_list.append(f"{key}: {json.dumps(value)}")

                        for principal in principals:
                            # 查询用户信息
                            try:
                                user = AliyunRAMUser.objects.filter(user_id=principal).first()
                                if user:
                                    display_name = user.display_name or user.user_principal_name or principal
                                    user_principal_name = user.user_principal_name or principal
                                else:
                                    display_name = principal
                                    user_principal_name = principal
                            except:
                                display_name = principal
                                user_principal_name = principal

                            user_info = {
                                'user_id': principal,
                                'display_name': display_name,
                                'user_principal_name': user_principal_name,
                                'actions': actions,
                                'resources': resources if isinstance(resources, list) else [resources],
                                'effect': effect,
                                'conditions': condition_list
                            }
                            principals_info.append(user_info)

                    return {
                        'policy_content': policy_content,
                        'is_public': policy_data.get('is_public', False),
                        'principals': principals_info
                    }

        except Exception as e:
            print(f"处理policy_info时出错: {e}")

        return {
            'policy_content': '',
            'is_public': False,
            'principals': []
        }

    def extract_principals(self, principal_data):
        principals = []
        print(f"原始principal数据: {principal_data}")
        print(f"数据类型: {type(principal_data)}")

        if not principal_data:
            return principals

        # 处理列表格式
        if isinstance(principal_data, list):
            print("处理列表格式的principal数据")
            principals.extend(principal_data)

        # 处理字符串格式
        elif isinstance(principal_data, str):
            print("处理字符串格式的principal数据")
            principals.append(principal_data)

        # 处理字典格式
        elif isinstance(principal_data, dict):
            print("处理字典格式的principal数据")
            # 阿里云RAM格式
            if 'RAM' in principal_data:
                ram_data = principal_data['RAM']
                if isinstance(ram_data, list):
                    principals.extend(ram_data)
                elif isinstance(ram_data, str):
                    principals.append(ram_data)

            # AWS格式
            elif 'AWS' in principal_data:
                aws_data = principal_data['AWS']
                if isinstance(aws_data, list):
                    principals.extend(aws_data)
                elif isinstance(aws_data, str):
                    principals.append(aws_data)

        # 去重
        unique_principals = list(set(principals))
        print(f"提取后的principals: {unique_principals}")
        return unique_principals


# ---------- 阿里云 RAM 用户 ----------
class AliyunRAMUserSerializer(serializers.ModelSerializer):
    create_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    update_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    last_login_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', allow_null=True)
    console_status = serializers.CharField(read_only=True)

    class Meta:
        model = AliyunRAMUser
        fields = '__all__'

class AliyunRAMUserDetailSerializer(AliyunRAMUserSerializer):
    """RAM用户详情序列化器，包含AccessKey详细信息"""
    class Meta(AliyunRAMUserSerializer.Meta):
        fields = '__all__'

# ---------- 阿里云 ECS ----------
class AliyunECSSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliyunECS
        fields = '__all__'


class ProjectAliyunecsSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )

    class Meta:
        model = ProjectAliyunecs
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


# ---------- 阿里云域名 ----------
class AliyunDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliyunDomain
        fields = '__all__'


class AliyunDNSRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliyunDNSRecord
        fields = '__all__'


class ProjectAliyunDomainSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )

    class Meta:
        model = ProjectAliyunDomain
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


# ---------- 阿里云安全组 ----------
class AliyunSecurityGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliyunSecurityGroup
        fields = '__all__'

class AliyunSecurityGroupRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliyunSecurityGroupRule
        fields = '__all__'


# ---------- 阿里云 SLB ----------
class AliyunSLBSerializer(serializers.ModelSerializer):
    creation_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = AliyunSLB
        fields = '__all__'

class AliyunSLBDetailSerializer(AliyunSLBSerializer):
    pass


class ProjectAliyunSLBSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )

    class Meta:
        model = ProjectAliyunSLB
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


# ---------- 阿里云 RDS ----------
class AliyunRDSSerializer(serializers.ModelSerializer):
    creation_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    expire_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', allow_null=True)

    class Meta:
        model = AliyunRDS
        exclude = ['read_only_instances', 'tags']

class AliyunRDSDetailSerializer(AliyunRDSSerializer):
    class Meta(AliyunRDSSerializer.Meta):
        fields = '__all__'


class ProjectAliyunRDSSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )

    class Meta:
        model = ProjectAliyunRDS
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


# ---------- 阿里云 EIP ----------
class AliyunEIPSerializer(serializers.ModelSerializer):
    allocation_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    expired_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', allow_null=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = AliyunEIP
        fields = '__all__'

class AliyunEIPDetailSerializer(AliyunEIPSerializer):
    pass


# ---------- 阿里云 WAF ----------
class AliyunWAFSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pay_type_display = serializers.CharField(source='get_pay_type_display', read_only=True)
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = AliyunWAF
        fields = [
            'instance_id', 'region_id', 'account_name',
            'status', 'status_display', 'pay_type', 'pay_type_display',
            'edition', 'start_time', 'end_time', 'updated_at',
            'capabilities', 'details'
        ]

    def get_capabilities(self, obj):
        return obj.capability_list


class AliyunWAFDetailSerializer(AliyunWAFSerializer):
    class Meta(AliyunWAFSerializer.Meta):
        fields = '__all__'


# ---------- 阿里云 NAS ----------
class AliyunNASSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = AliyunNAS
        fields = '__all__'

class AliyunNASDetailSerializer(AliyunNASSerializer):
    pass


class ProjectAliyunNASSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )

    class Meta:
        model = ProjectAliyunNAS
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }



class ProjectAliyunSLSSerializer(serializers.ModelSerializer):
    environment_display = serializers.CharField(
        source='get_environment_display',
        read_only=True
    )

    class Meta:
        model = ProjectAliyunSLS
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class AliyunDNSRecordSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='domain.account_name', read_only=True)


    class Meta:
        model = AliyunDNSRecord
        fields = '__all__'

class AliyunSNATEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = AliyunSNATEntry
        fields = '__all__'



class AliyunSLSLogStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = AliyunSLSLogStore
        fields = '__all__'

class AliyunSLSProjectSerializer(serializers.ModelSerializer):
    # 移除了冗余的 source 参数
    logstores = AliyunSLSLogStoreSerializer(many=True, read_only=True)

    class Meta:
        model = AliyunSLSProject
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 时间格式化（和 RDS/WAF 一致）
        for f in ('create_time', 'last_modify_time', 'updated_at'):
            if getattr(instance, f):
                data[f] = getattr(instance, f).strftime('%Y-%m-%d %H:%M:%S')
        return data


class AliyunSecurityGroupSerializer(serializers.ModelSerializer):
    tags = serializers.JSONField(default=dict)

    class Meta:
        model = AliyunSecurityGroup
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AliyunSecurityGroupRuleSerializer(serializers.ModelSerializer):
    security_group_name = serializers.CharField(source='security_group.security_group_name', read_only=True)
    security_group_id = serializers.CharField(source='security_group.security_group_id', read_only=True)

    class Meta:
        model = AliyunSecurityGroupRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']