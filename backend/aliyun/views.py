import logging
from django.utils import timezone

from alibabacloud_tea_openapi.exceptions import ClientException
from django.db import transaction

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import generics, filters, viewsets, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView

from .models import (
    AliyunOSS, AliyunRAMUser, AliyunECS, ProjectAliyunecs, AliyunDNSRecord, AliyunDomain, ProjectAliyunDomain,
    AliyunSecurityGroup, AliyunSecurityGroupRule, AliyunSLB, ProjectAliyunSLB, AliyunRDS, ProjectAliyunRDS, AliyunEIP, AliyunWAF, AliyunWAF, AliyunNAS, ProjectAliyunNAS,
    AliyunSNATEntry, AliyunSLSProject, AliyunSLSLogStore, ProjectAliyunSLS
)

from .serializers import (
    AliyunOSSSerializer, AliyunRAMUserSerializer, OSSBucketDetailSerializer, AliyunECSSerializer,
    ProjectAliyunecsSerializer, AliyunDomainSerializer, ProjectAliyunDomainSerializer, AliyunSLBSerializer, ProjectAliyunSLBSerializer,
    AliyunWAFSerializer, AliyunNASSerializer, ProjectAliyunNASSerializer, AliyunRDSSerializer, ProjectAliyunRDSSerializer, AliyunEIPSerializer, AliyunSNATEntrySerializer,
    AliyunDNSRecordSerializer, AliyunSecurityGroupSerializer, AliyunSecurityGroupRuleSerializer,
    AliyunSLSProjectSerializer, ProjectAliyunSLSSerializer
)




from .aliyun_common import convert_utc_to_shanghai, get_aliyun_accounts, make_tea_config

from alibabacloud_tea_util.client import Client as UtilClient
from Tea.exceptions import TeaException
from alibabacloud_tea_util.models import RuntimeOptions
from Tea.exceptions import TeaException

# 导入各服务客户端
import alibabacloud_oss_v2 as oss
from alibabacloud_oss_v2 import credentials
from alibabacloud_oss_v2.client import Client as OssClient
from alibabacloud_oss_v2.models import (
    GetBucketInfoRequest, GetBucketStatRequest, ListBucketsRequest,
    GetBucketPolicyRequest, ListCnameRequest, GetBucketPolicyStatusRequest
)

from alibabacloud_ram20150501.client import Client as RamClient
from alibabacloud_ram20150501.models import (
    ListUsersRequest, GetUserRequest, ListGroupsForUserRequest,
    ListAccessKeysRequest, ListPoliciesForUserRequest
)

from alibabacloud_ims20190815.client import Client as ImsClient
from alibabacloud_ims20190815.models import (
    ListUsersRequest as ImsListUsersRequest,
    ListAccessKeysRequest as ImsListAccessKeysRequest,
    GetAccessKeyLastUsedRequest
)
from alibabacloud_ram20150501.models import (
    ListGroupsForUserRequest,
    ListPoliciesForUserRequest
)

from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_ecs20140526.models import (
    DescribeInstancesRequest,
    DescribeDisksRequest
)

from alibabacloud_domain20180129.client import Client as DomainClient
from alibabacloud_alidns20150109.client import Client as DnsClient
from alibabacloud_alidns20150109.models import DescribeDomainRecordsRequest
from alibabacloud_domain20180129.models import QueryDomainListRequest, QueryDomainByDomainNameRequest


from alibabacloud_slb20140515.client import Client as SlbClient
from alibabacloud_slb20140515.models import (
    DescribeLoadBalancersRequest, DescribeLoadBalancerAttributeRequest,
    DescribeLoadBalancerListenersRequest,
    DescribeVServerGroupsRequest, DescribeVServerGroupAttributeRequest
)

from alibabacloud_rds20140815.client import Client as Rds20140815Client
from alibabacloud_rds20140815 import models as rds_models

from aliyun.aliyun_common import get_aliyun_accounts, convert_utc_to_shanghai, safe_api_call
from django.utils import timezone as django_timezone
from alibabacloud_tea_openapi import models as open_api_models

from alibabacloud_vpc20160428.client import Client as VpcClient
from alibabacloud_vpc20160428.models import DescribeEipAddressesRequest, DescribeSnatTableEntriesRequest, DescribeNatGatewaysRequest
from alibabacloud_nas20170626.client import Client as NasClient
from alibabacloud_nas20170626.models import DescribeFileSystemsRequest
from alibabacloud_waf_openapi20211001.client import Client as WafClient
from alibabacloud_waf_openapi20211001.models import DescribeInstanceRequest
from alibabacloud_sls20201230.client import Client as Sls20201230Client
from alibabacloud_sls20201230 import models as sls_models
from alibabacloud_tea_util import models as util_models


import threading

from .models import AliyunECS, ProjectAliyunecs
from .serializers import AliyunECSSerializer
from .filters import AliyunECSFilter, AliyunDNSRecordFilter
from apps.utils.pagination import CustomPagination
from apps.utils.formatdatetime import formatdatetime
from apps.utils.response import ApiResponse

from typing import Any, Optional
import json
import time
import csv
from django.http import HttpResponse


logger = logging.getLogger(__name__)



class SyncActionMixin:
    @action(detail=False, methods=['post', 'get'])
    def sync(self, request):
        raise NotImplementedError("请在子类实现 sync 方法")


# -------------------- 阿里云 OSS --------------------
class AliyunOSSViewSet(viewsets.ModelViewSet):
    queryset = AliyunOSS.objects.all()
    serializer_class = AliyunOSSSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'name', 'region', 'storage_class', 'versioning',
        'transfer_acceleration', 'acl', 'redundancy_type', 'account_name'
    ]
    search_fields = ['name', 'tags']
    ordering = ['-creation_date']
    lookup_field = 'name'

    # ---------- 内部工具 ----------
    def _build_oss_client(self, account: dict, region: str) -> oss.Client:
        clean_region = region.replace('oss-', '')
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials.StaticCredentialsProvider(
            access_key_id=account['access_key'],
            access_key_secret=account['access_secret']
        )
        cfg.region = clean_region
        cfg.endpoint = f"https://oss-{clean_region}.aliyuncs.com"
        return oss.Client(cfg)

    def _get_bucket_policy_info(self, client, bucket_name):
        """获取Bucket策略信息"""
        try:
            request = GetBucketPolicyRequest(bucket=bucket_name)
            result = client.get_bucket_policy(request)
            policy_content = result.body

            # 获取策略状态
            try:
                status_request = GetBucketPolicyStatusRequest(bucket=bucket_name)
                status_result = client.get_bucket_policy_status(status_request)
                is_public = status_result.policy_status.is_public if status_result.policy_status else False
            except Exception as status_error:
                # 策略状态获取失败，默认为非公开
                logger.debug(f"获取Bucket策略状态失败 {bucket_name}: {status_error}")
                is_public = False

            return {
                'policy_content': policy_content,
                'is_public': is_public
            }
        except Exception as e:
            # 检查是否是"策略不存在"的错误
            if "NoSuchBucketPolicy" in str(e) or "404" in str(e):
                logger.debug(f"Bucket {bucket_name} 没有设置策略")
                return {'policy_content': None, 'is_public': False}
            else:
                logger.warning(f"获取Bucket策略失败 {bucket_name}: {e}")
                return {'policy_content': None, 'is_public': False}

    def _get_cname_records(self, client, bucket_name):
        """获取CNAME记录"""
        try:
            request = ListCnameRequest(bucket=bucket_name)
            result = client.list_cname(request)

            cname_records = []
            if result.cnames:
                for cname in result.cnames:
                    record = {
                        'domain': cname.domain,
                        'last_modified': cname.last_modified,
                        'status': cname.status
                    }

                    if cname.certificate:
                        record['certificate'] = {
                            'fingerprint': cname.certificate.fingerprint,
                            'valid_start_date': cname.certificate.valid_start_date,
                            'valid_end_date': cname.certificate.valid_end_date,
                            'type': cname.certificate.type,
                            'cert_id': cname.certificate.cert_id,
                            'status': cname.certificate.status,
                            'creation_date': cname.certificate.creation_date
                        }

                    cname_records.append(record)

            return cname_records
        except Exception as e:
            # 检查是否是CNAME不存在的错误
            if "404" in str(e) or "not exist" in str(e).lower():
                logger.debug(f"Bucket {bucket_name} 没有CNAME记录")
                return []
            else:
                logger.warning(f"获取CNAME记录失败 {bucket_name}: {e}")
                return []

    # ---------- 同步 ----------
    @action(detail=False, methods=['post', 'get'])
    def sync(self, request):
        logger.info("开始 OSS 同步")
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置账号'}, status=400)

        total = 0
        for acc in accounts:
            logger.info(f"同步账号: {acc['name']}")
            for region in acc['regions']:
                try:
                    client = self._build_oss_client(acc, region)
                    buckets = client.list_buckets(oss.ListBucketsRequest()).buckets or []
                    logger.info(f"账号 {acc['name']} 在区域 {region} 发现 {len(buckets)} 个 Bucket")

                    for b in buckets:
                        try:
                            real_region = (b.location or region).replace('oss-', '')
                            client = self._build_oss_client(acc, real_region)

                            logger.info(f"正在同步Bucket: {b.name}, 区域: {real_region}")

                            # 获取Bucket基本信息
                            info_result = client.get_bucket_info(oss.GetBucketInfoRequest(bucket=b.name))
                            info = info_result.bucket_info

                            # 获取Bucket统计信息
                            stat_result = client.get_bucket_stat(oss.GetBucketStatRequest(bucket=b.name))
                            stat = stat_result

                            # 获取策略信息（这里会处理404错误）
                            policy_info = self._get_bucket_policy_info(client, b.name)

                            # 获取CNAME记录
                            cname_records = self._get_cname_records(client, b.name)

                            defaults = {
                                'name': b.name,
                                'region': real_region,
                                'storage_class': info.storage_class,
                                'creation_date': convert_utc_to_shanghai(info.creation_date),
                                'redundancy_type': info.data_redundancy_type,
                                'versioning': getattr(info, 'versioning', 'Disabled'),
                                'transfer_acceleration': getattr(info, 'transfer_acceleration', 'Disabled'),
                                'acl': getattr(info, 'acl', 'private'),
                                'owner_id': info.owner.id if info.owner else None,
                                'owner_display_name': info.owner.display_name if info.owner else None,
                                'storage': int(stat.storage or 0),
                                'object_count': int(stat.object_count or 0),
                                'standard_storage': int(stat.standard_storage or 0),
                                'ia_storage': int(stat.infrequent_access_storage or 0),
                                'archive_storage': int(stat.archive_storage or 0),
                                'cold_archive_storage': int(stat.cold_archive_storage or 0),
                                'deep_cold_archive_storage': int(stat.deep_cold_archive_storage or 0),
                                'monthly_flow': int(getattr(stat, 'monthly_flow', 0) or 0),
                                'monthly_access_count': int(getattr(stat, 'monthly_access_count', 0) or 0),
                                'account_name': acc['name'],

                                # 新增字段
                                'data_redundancy_type': info.data_redundancy_type,
                                'resource_group_id': getattr(b, 'resource_group_id', None),
                                'extranet_endpoint': getattr(b, 'extranet_endpoint', ''),
                                'intranet_endpoint': getattr(b, 'intranet_endpoint', ''),

                                # 可选字段
                                'access_monitor': getattr(info, 'access_monitor', 'Disabled'),
                                'sse_algorithm': getattr(info, 'sse_algorithm', None),
                                'kms_master_key_id': getattr(info, 'kms_master_key_id', None),
                                'cross_region_replication': getattr(info, 'cross_region_replication', 'Disabled'),
                                'block_public_access': getattr(info, 'block_public_access', 'Disabled'),
                                'archive_direct_read': getattr(info, 'archive_direct_read', 'Disabled'),

                                # 统计字段
                                'infrequent_access_storage': int(stat.infrequent_access_storage or 0),
                                'infrequent_access_real_storage': int(
                                    getattr(stat, 'infrequent_access_real_storage', 0) or 0),
                                'infrequent_access_object_count': int(
                                    getattr(stat, 'infrequent_access_object_count', 0) or 0),
                                'archive_real_storage': int(getattr(stat, 'archive_real_storage', 0) or 0),
                                'archive_object_count': int(getattr(stat, 'archive_object_count', 0) or 0),
                                'cold_archive_real_storage': int(getattr(stat, 'cold_archive_real_storage', 0) or 0),
                                'cold_archive_object_count': int(getattr(stat, 'cold_archive_object_count', 0) or 0),
                                'deep_cold_archive_real_storage': int(
                                    getattr(stat, 'deep_cold_archive_real_storage', 0) or 0),
                                'deep_cold_archive_object_count': int(
                                    getattr(stat, 'deep_cold_archive_object_count', 0) or 0),
                                'multipart_upload_count': int(getattr(stat, 'multipart_upload_count', 0) or 0),
                                'delete_marker_count': int(getattr(stat, 'delete_marker_count', 0) or 0),

                                # 策略和CNAME信息存储为JSON
                                'tags': {'policy': policy_info, 'cname': cname_records}
                            }

                            # 过滤掉模型中不存在的字段
                            model_fields = [f.name for f in AliyunOSS._meta.get_fields()]
                            valid_fields = {k: v for k, v in defaults.items() if k in model_fields}

                            AliyunOSS.objects.update_or_create(name=b.name, defaults=valid_fields)
                            total += 1
                            logger.info(f"同步Bucket成功: {b.name}")

                        except Exception as e:
                            logger.error(f"同步Bucket {b.name} 失败: {e}")
                            continue

                except Exception as e:
                    logger.exception(f"同步区域 {region} 失败: {e}")
                    continue

        logger.info(f"OSS 同步完成，共 {total} 条")
        return Response({'status': 'success', 'count': total})

    # ---------- 获取单个 Bucket 用量 ----------
    @action(detail=True, methods=['get'])
    def usage(self, request, name=None):
        """获取特定 Bucket 的使用情况"""
        try:
            bucket = self.get_object()
            logger.debug(f"获取使用情况: {bucket}")
            usage_data = {
                'storage': bucket.storage,
                'standard_storage': bucket.standard_storage,
                'ia_storage': bucket.ia_storage,
                'archive_storage': bucket.archive_storage,
                'cold_archive_storage': bucket.cold_archive_storage,
                'deep_cold_archive_storage': bucket.deep_cold_archive_storage,
                'monthly_flow': bucket.monthly_flow,
                'monthly_access_count': bucket.monthly_access_count,
                'object_count': bucket.object_count,
                'infrequent_access_storage': bucket.infrequent_access_storage,
                'archive_real_storage': bucket.archive_real_storage,
                'cold_archive_real_storage': bucket.cold_archive_real_storage,
                'deep_cold_archive_real_storage': bucket.deep_cold_archive_real_storage,
                'multipart_upload_count': bucket.multipart_upload_count,
                'delete_marker_count': bucket.delete_marker_count
            }
            return Response(usage_data)
        except AliyunOSS.DoesNotExist:
            logger.debug("Bucket不存在")
            return Response({"error": "Bucket不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.debug(f"获取使用情况失败: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------- 获取Bucket详细信息 ----------
    @action(detail=True, methods=['get'])
    def detailed_info(self, request, name=None):
        """获取Bucket的详细信息"""
        try:
            bucket = self.get_object()
            accounts = get_aliyun_accounts()

            if not accounts:
                return Response({"error": "未配置账号"}, status=status.HTTP_400_BAD_REQUEST)

            # 找到对应的账号
            account = None
            for acc in accounts:
                if acc['name'] == bucket.account_name:
                    account = acc
                    break

            if not account:
                return Response({"error": "未找到对应的账号配置"}, status=status.HTTP_400_BAD_REQUEST)

            # 创建客户端并获取实时信息
            client = self._build_oss_client(account, bucket.region)

            # 获取实时统计信息
            stat_result = client.get_bucket_stat(oss.GetBucketStatRequest(bucket=bucket.name))
            stat = stat_result

            # 获取策略信息
            policy_info = self._get_bucket_policy_info(client, bucket.name)

            # 获取CNAME记录
            cname_records = self._get_cname_records(client, bucket.name)

            detailed_info = {
                'basic_info': {
                    'name': bucket.name,
                    'region': bucket.region,
                    'storage_class': bucket.storage_class,
                    'creation_date': bucket.creation_date,
                    'acl': bucket.acl,
                    'versioning': bucket.versioning,
                    'transfer_acceleration': bucket.transfer_acceleration,
                    'access_monitor': bucket.access_monitor,
                    'block_public_access': bucket.block_public_access,
                    'archive_direct_read': bucket.archive_direct_read
                },
                'stat_info': {
                    'storage': stat.storage,
                    'object_count': stat.object_count,
                    'standard_storage': stat.standard_storage,
                    'infrequent_access_storage': stat.infrequent_access_storage,
                    'archive_storage': stat.archive_storage,
                    'cold_archive_storage': stat.cold_archive_storage,
                    'deep_cold_archive_storage': stat.deep_cold_archive_storage,
                    'monthly_flow': getattr(stat, 'monthly_flow', 0),
                    'monthly_access_count': getattr(stat, 'monthly_access_count', 0)
                },
                'policy_info': policy_info,
                'cname_info': cname_records
            }

            return Response(detailed_info)

        except AliyunOSS.DoesNotExist:
            return Response({"error": "Bucket不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"获取详细信息失败: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OSSBucketDetailView(APIView):
    """
    OSS Bucket详情视图
    """
    def get(self, request, bucket_name):  # 使用bucket_name参数名来匹配URL路由
        """
        获取Bucket详情
        """
        try:
            # 使用name字段作为主键查询
            bucket = AliyunOSS.objects.get(name=bucket_name)
            serializer = OSSBucketDetailSerializer(bucket)
            return Response({
                'code': 200,
                'msg': 'success',
                'data': serializer.data
            })
        except AliyunOSS.DoesNotExist:
            return Response({
                'code': 404,
                'msg': 'Bucket not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'msg': f'Server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------- 阿里云 RAM --------------------
def safe_get_attr(obj, attr_name: str, default: Any = None) -> Any:
    """
    安全获取对象属性，避免属性不存在时抛出异常
    """
    try:
        if hasattr(obj, attr_name):
            value = getattr(obj, attr_name)
            if value is None or value == "":
                return default
            return value
        elif isinstance(obj, dict) and attr_name in obj:
            value = obj[attr_name]
            if value is None or value == "":
                return default
            return value
        else:
            return default
    except Exception as e:
        logger.debug(f"获取属性 {attr_name} 失败: {e}")
        return default

def safe_extract_list(response, main_attr: str, sub_attr: Optional[str] = None, default: Any = None) -> list:
    """
    安全地从响应中提取列表数据
    """
    if default is None:
        default = []

    if not response or not hasattr(response, 'body'):
        return default

    body = response.body

    if not hasattr(body, main_attr):
        logger.debug(f"响应体缺少属性: {main_attr}")
        return default

    main_obj = getattr(body, main_attr)

    if sub_attr:
        if hasattr(main_obj, sub_attr):
            sub_obj = getattr(main_obj, sub_attr)
            if isinstance(sub_obj, list):
                return sub_obj
            else:
                logger.debug(f"子属性 {sub_attr} 不是列表类型: {type(sub_obj)}")
                return default
        else:
            logger.debug(f"主对象缺少子属性: {sub_attr}")
            return default

    if isinstance(main_obj, list):
        return main_obj

    try:
        if hasattr(main_obj, 'to_map'):
            obj_map = main_obj.to_map()
            for possible_key in ['access_key', 'key', 'items', 'data', 'list']:
                if possible_key in obj_map and isinstance(obj_map[possible_key], list):
                    return obj_map[possible_key]
    except Exception as e:
        logger.debug(f"转换对象到列表失败: {e}")

    return default

def debug_response_structure(response, api_name: str):
    """调试API响应结构"""
    if not response or not response.body:
        logger.debug(f"{api_name}: 响应体为空")
        return

    body = response.body
    logger.debug(f"{api_name} 响应体类型: {type(body)}")

    if hasattr(body, 'to_map'):
        try:
            body_map = body.to_map()
            logger.debug(f"{api_name} 响应体内容: {json.dumps(body_map, indent=2, ensure_ascii=False)}")
        except Exception as e:
            logger.debug(f"{api_name} 转换响应体失败: {e}")

    logger.debug(f"{api_name} 响应体属性: {[attr for attr in dir(body) if not attr.startswith('_')]}")

class AliyunRAMUserViewSet(viewsets.ReadOnlyModelViewSet, SyncActionMixin):
    queryset = AliyunRAMUser.objects.all()
    serializer_class = AliyunRAMUserSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['account_name', 'active', 'mfa_enabled', 'user_principal_name', 'display_name']
    search_fields = ['display_name', 'email', 'mobile_phone', 'user_principal_name']
    ordering = ['-update_date']



    @action(detail=False, methods=['post'])
    def sync(self, request):
        logger.info('开始同步 RAM 用户（使用IMS API）')
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置账号'}, status=400)

        total = 0
        for acc in accounts:
            region = acc['regions'][0] if acc['regions'] else 'cn-hangzhou'

            try:
                ims_cfg = make_tea_config(acc, region, 'ims')
                ims_client = ImsClient(ims_cfg)
                ram_cfg = make_tea_config(acc, region, 'ram')
                ram_client = RamClient(ram_cfg)
                runtime = RuntimeOptions()

                ims_req = ImsListUsersRequest()
                ims_req.max_results = 100
                marker = None
                page_count = 0

                while True:
                    page_count += 1
                    logger.info(f"正在获取账号 {acc['name']} 的第 {page_count} 页IMS用户数据")

                    if marker:
                        ims_req.marker = marker

                    try:
                        ims_resp = ims_client.list_users_with_options(ims_req, runtime)

                        # 使用安全方法提取用户列表
                        users = safe_extract_list(ims_resp, 'users', 'user')

                        if not users:
                            logger.info(f"账号 {acc['name']} 没有更多IMS用户数据")
                            break

                        logger.info(f"账号 {acc['name']} 第 {page_count} 页获取到 {len(users)} 个IMS用户")

                        for user in users:
                            user_id = safe_get_attr(user, 'user_id', '')
                            user_principal_name = safe_get_attr(user, 'user_principal_name', '')

                            # ******* 添加验证：跳过无效用户 *******
                            if not user_id or not user_principal_name:
                                logger.warning(
                                    f"跳过无效用户数据: user_id={user_id}, principal_name={user_principal_name}")
                                continue
                            # *************************************

                            logger.debug(f"处理用户: {user_principal_name} (ID: {user_id})")

                            if not user_id:
                                continue

                            # 获取访问密钥、用户组和策略信息
                            access_keys = self._get_user_access_keys(ims_client, user_principal_name)
                            groups = self._get_user_groups(ram_client, user_principal_name)
                            policies = self._get_user_policies(ram_client, user_principal_name)

                            # 直接使用原始字符串，不进行任何转换 - 与AliyunOSSViewSet完全一致
                            create_date = safe_get_attr(user, 'create_date', None)
                            update_date = safe_get_attr(user, 'update_date', None)
                            last_login_date = safe_get_attr(user, 'last_login_date', None)

                            # 处理标签信息
                            tags = []
                            if hasattr(user, 'tags') and hasattr(user.tags, 'tag'):
                                tags = [
                                    {
                                        'tag_key': safe_get_attr(tag, 'tag_key', ''),
                                        'tag_value': safe_get_attr(tag, 'tag_value', '')
                                    }
                                    for tag in user.tags.tag
                                ]

                            # 获取控制台访问状态
                            console_status = self._get_user_console_status_ims(ims_client, user_principal_name)
                            logger.info(f"用户 {user_principal_name} 最终控制台状态: {console_status}")

                            # 获取原始时间字符串
                            create_date_raw = safe_get_attr(user, 'create_date', None)
                            update_date_raw = safe_get_attr(user, 'update_date', None)
                            last_login_date_raw = safe_get_attr(user, 'last_login_date', None)

                            # 转换为上海时间
                            create_date = convert_utc_to_shanghai(create_date_raw) if create_date_raw else None
                            update_date = convert_utc_to_shanghai(update_date_raw) if update_date_raw else None
                            last_login_date = convert_utc_to_shanghai(
                                last_login_date_raw) if last_login_date_raw else None

                            # 构建defaults字典 - 使用转换后的时间
                            defaults = {
                                'user_name': safe_get_attr(user, 'user_name', ''),
                                'user_principal_name': user_principal_name,
                                'display_name': safe_get_attr(user, 'display_name', ''),
                                'account_name': acc['name'],
                                'email': safe_get_attr(user, 'email', ''),
                                'mobile_phone': safe_get_attr(user, 'mobile_phone', ''),
                                'comments': safe_get_attr(user, 'comments', ''),
                                'create_date': create_date,  # 转换后的上海时间
                                'update_date': update_date,  # 转换后的上海时间
                                'last_login_date': last_login_date,  # 转换后的上海时间
                                'status': safe_get_attr(user, 'status', 'active'),
                                'active': safe_get_attr(user, 'status', '').lower() == 'active',
                                'provision_type': safe_get_attr(user, 'provision_type', 'Manual'),
                                'access_keys_count': len(access_keys),
                                'access_keys': access_keys,
                                'groups': groups,
                                'attached_policies': policies,
                                'tags': tags,
                                'console_status': console_status,
                            }

                            # 移除None值
                            defaults = {k: v for k, v in defaults.items() if v is not None}

                            # 使用与AliyunOSSViewSet完全相同的update_or_create方法
                            AliyunRAMUser.objects.update_or_create(
                                user_id=user_id,
                                defaults=defaults
                            )
                            total += 1

                        # 检查是否还有更多数据
                        is_truncated = safe_get_attr(ims_resp.body, 'is_truncated', False)
                        marker = safe_get_attr(ims_resp.body, 'marker', None)

                        if not is_truncated or not marker:
                            logger.info(f"账号 {acc['name']} 的IMS用户数据已全部获取")
                            break

                        time.sleep(0.5)

                    except TeaException as e:
                        logger.error(f"IMS API调用失败: {e}")
                        break
                    except Exception as e:
                        logger.error(f"处理IMS用户数据时发生异常: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        break

            except Exception as e:
                logger.error(f"处理账号 {acc['name']} 时发生异常: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue

        logger.info(f'RAM 用户同步完成，共 {total} 条')
        return Response({'status': 'success', 'count': total})

    def _get_user_access_keys(self, ims_client, user_principal_name):
        """获取用户访问密钥列表"""
        access_keys = []

        if not user_principal_name:
            logger.warning("用户主体名称为空，无法获取访问密钥")
            return access_keys

        try:
            req = ImsListAccessKeysRequest()
            req.user_principal_name = user_principal_name
            runtime = RuntimeOptions()
            resp = ims_client.list_access_keys_with_options(req, runtime)

            debug_response_structure(resp, f"ListAccessKeys({user_principal_name})")

            access_key_list = safe_extract_list(resp, 'access_keys', 'access_key')
            logger.info(f"用户 {user_principal_name} 解析到 {len(access_key_list)} 个访问密钥")

            for ak in access_key_list:
                access_key_id = safe_get_attr(ak, 'access_key_id', '')

                # ****** 修改：即使ID为空也记录其他信息 ******
                if not access_key_id:
                    logger.warning(f"用户 {user_principal_name} 存在AccessKey ID为空，仍记录其他信息")

                status = safe_get_attr(ak, 'status', '')
                create_date_raw = safe_get_attr(ak, 'create_date', None)
                update_date_raw = safe_get_attr(ak, 'update_date', None)

                # 转换时间格式（返回datetime对象）
                create_date = convert_utc_to_shanghai(create_date_raw) if create_date_raw else None
                update_date = convert_utc_to_shanghai(update_date_raw) if update_date_raw else None

                last_used_info = self._get_access_key_last_used(ims_client, user_principal_name, access_key_id)
                last_used_date_raw = last_used_info.get('last_used_date')
                last_used_date = convert_utc_to_shanghai(last_used_date_raw) if last_used_date_raw else None

                # 在存入JSONField前，将datetime对象转为字符串
                access_key_data = {
                    'access_key_id': access_key_id or 'UNKNOWN',  # 空值处理
                    'status': status,
                    'create_date': create_date.strftime('%Y-%m-%d %H:%M:%S') if create_date else None,
                    'update_date': update_date.strftime('%Y-%m-%d %H:%M:%S') if update_date else None,
                    'last_used_date': last_used_date.strftime('%Y-%m-%d %H:%M:%S') if last_used_date else None,
                    'service_name': last_used_info.get('service_name')
                }

                # 移除None值
                access_key_data = {k: v for k, v in access_key_data.items() if v is not None}
                access_keys.append(access_key_data)

            return access_keys

        except TeaException as e:
            error_msg = str(e)
            if any(keyword in error_msg for keyword in ['EntityNotExist', 'NotFound', 'NotExist', '不存在']):
                logger.info(f"用户 {user_principal_name} 没有访问密钥或不存在")
            else:
                logger.error(f"获取用户 {user_principal_name} 访问密钥失败 (TeaException): {error_msg}")
        except Exception as e:
            logger.error(f"获取用户 {user_principal_name} 访问密钥时发生未知异常: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return access_keys

    def _get_access_key_last_used(self, ims_client, user_principal_name, access_key_id):
        """获取访问密钥的最后使用信息"""
        try:
            req = GetAccessKeyLastUsedRequest()
            req.user_access_key_id = access_key_id
            if user_principal_name:
                req.user_principal_name = user_principal_name

            runtime = RuntimeOptions()
            resp = ims_client.get_access_key_last_used_with_options(req, runtime)

            if resp.body and hasattr(resp.body, 'access_key_last_used'):
                last_used = resp.body.access_key_last_used

                # ****** 安全获取原始值 ******
                last_used_date_raw = safe_get_attr(last_used, 'last_used_date', None)

                # ****** 检查是否为"N/A" ******
                if last_used_date_raw and str(last_used_date_raw).strip().upper() == 'N/A':
                    logger.debug(f"访问密钥 {access_key_id} 从未被使用")
                    last_used_date_raw = None

                return {
                    'last_used_date': last_used_date_raw,  # 保持原始字符串或None
                    'service_name': safe_get_attr(last_used, 'service_name', '')
                }

        except Exception as e:
            logger.error(f"获取访问密钥 {access_key_id} 最后使用信息失败: {e}")

        return {'last_used_date': None, 'service_name': ''}

    def _get_user_groups(self, ram_client, user_principal_name):
        """获取用户所属组"""
        try:
            req = ListGroupsForUserRequest()
            if user_principal_name and '@' in user_principal_name:
                user_name = user_principal_name.split('@')[0]
                req.user_name = user_name
            else:
                req.user_name = user_principal_name

            runtime = RuntimeOptions()
            resp = ram_client.list_groups_for_user_with_options(req, runtime)

            # 使用安全方法提取组列表
            group_list = safe_extract_list(resp, 'groups', 'group')

            return [{
                'group_name': safe_get_attr(g, 'group_name', ''),
                'comments': safe_get_attr(g, 'comments', '')
            } for g in group_list]

        except Exception as e:
            logger.error(f"获取用户 {user_principal_name} 所属组失败: {e}")

        return []

    def _get_user_policies(self, ram_client, user_principal_name):
        """获取用户附加策略"""
        try:
            req = ListPoliciesForUserRequest()
            if user_principal_name and '@' in user_principal_name:
                user_name = user_principal_name.split('@')[0]
                req.user_name = user_name
            else:
                req.user_name = user_principal_name

            runtime = RuntimeOptions()
            resp = ram_client.list_policies_for_user_with_options(req, runtime)

            # 使用安全方法提取策略列表
            policy_list = safe_extract_list(resp, 'policies', 'policy')

            return [{
                'policy_name': safe_get_attr(p, 'policy_name', ''),
                'policy_type': safe_get_attr(p, 'policy_type', ''),
                'description': safe_get_attr(p, 'description', ''),
                'attach_date': formatdatetime(safe_get_attr(p, 'attach_date', None))
            } for p in policy_list]

        except Exception as e:
            logger.error(f"获取用户 {user_principal_name} 策略失败: {e}")

        return []

    def retrieve(self, request, *args, **kwargs):
        """获取用户详情"""
        instance = self.get_object()
        serializer = AliyunRAMUserDetailSerializer(instance)
        return Response(serializer.data)

    def _get_user_console_status_ims(self, ims_client, user_principal_name):
        """使用IMS API获取用户控制台状态"""
        try:
            from alibabacloud_ims20190815.models import GetLoginProfileRequest

            logger.debug(f"使用IMS API获取用户 {user_principal_name} 的控制台状态")

            req = GetLoginProfileRequest()
            req.user_principal_name = user_principal_name

            runtime = RuntimeOptions()
            resp = ims_client.get_login_profile_with_options(req, runtime)

            # 详细调试信息
            if resp.body:
                logger.debug(f"IMS完整响应: {resp.body.to_map()}")

                if hasattr(resp.body, 'login_profile'):
                    login_profile = resp.body.login_profile
                    logger.debug(f"IMS登录配置: {login_profile.to_map() if hasattr(login_profile, 'to_map') else login_profile}")

                    # 从IMS响应中获取状态
                    if hasattr(login_profile, 'status'):
                        status = login_profile.status
                        logger.info(f"IMS控制台状态: {status}")

                        # 状态映射
                        if status == 'Active':
                            return '已开启'
                        elif status == 'Inactive':
                            return '已禁用'
                        else:
                            logger.warning(f"未知状态值: {status}")
                            return f'未知状态({status})'
                    else:
                        logger.warning("IMS登录配置中没有status字段")
                        return '已开启'  # 默认视为已开启
                else:
                    logger.warning("IMS响应中没有login_profile字段")
                    return '已开启'  # 默认视为已开启
            else:
                logger.warning("IMS响应体为空")
                return '未开启'

        except TeaException as e:
            error_msg = str(e)
            error_code = getattr(e, 'code', '未知错误码')

            logger.debug(f"IMS错误详情: code={error_code}, message={error_msg}")

            # IMS API的错误类型判断
            not_found_errors = [
                'EntityNotExist', 'NotFound', 'NoSuch',
                'NotExist', 'NoLoginProfile', 'EntityNotExists.User'
            ]

            if any(error in error_msg for error in not_found_errors) or error_code in ['EntityNotExist.User',
                                                                                       'EntityNotExist.LoginProfile']:
                logger.info(f"用户 {user_principal_name} 未开启控制台访问（无登录配置）")
                return '未开启'
            elif 'Forbidden' in error_msg or 'Permission' in error_msg or error_code in ['Forbidden', 'AccessDenied']:
                logger.warning(f"权限不足，无法获取用户 {user_principal_name} 的控制台状态")
                return '权限不足'
            else:
                logger.error(f"IMS获取控制台状态失败: {error_code} - {error_msg}")
                return f'API错误: {error_code}'

        except Exception as e:
            logger.error(f"IMS获取控制台访问状态时发生异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return '获取失败'

    @action(detail=False, methods=['get'])
    def export(self, request):
        """导出RAM用户数据为CSV"""
        queryset = self.filter_queryset(self.get_queryset())

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="ram_users.csv"'

        writer = csv.writer(response)
        # 写入表头
        writer.writerow([
            '用户ID', '用户名', '登录名称', '显示名称', '所属账号', '邮箱',
            '手机号', '账号状态', 'MFA状态', '控制台状态', '访问密钥数量',
            '创建时间', '更新时间', '最后登录时间'
        ])

        # 写入数据
        for user in queryset:
            writer.writerow([
                user.user_id or '',
                user.user_name or '',
                user.user_principal_name or '',
                user.display_name or '',
                user.account_name or '',
                user.email or '',
                user.mobile_phone or '',
                '激活' if user.active else '禁用',
                '已启用' if user.mfa_enabled else '未启用',
                user.console_status or '未知',
                user.access_keys_count or 0,
                user.create_date.strftime('%Y-%m-%d %H:%M:%S') if user.create_date else '',
                user.update_date.strftime('%Y-%m-%d %H:%M:%S') if user.update_date else '',
                user.last_login_date.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_date else ''
            ])

        return response

    @action(detail=False, methods=['get'])
    def simple_list(self, request):
        """获取简化的用户列表（用于前端选择）"""
        users = AliyunRAMUser.objects.all().values(
            'user_id', 'user_name', 'user_principal_name', 'display_name', 'account_name'
        )
        return Response({
            'code': 200,
            'msg': 'success',
            'data': list(users)
        })


# -------------------- 阿里云 ECS --------------------
class AliyunECSListViewSet(viewsets.ModelViewSet):
    """
    阿里云ECS资产管理（SDK v2 完整版）
    - 列表/过滤/分页
    - 一键同步（/ecs/sync/ POST）
    - 多账号/跨地域/磁盘详情/项目映射
    """
    queryset = AliyunECS.objects.all().order_by('-creation_time')
    serializer_class = AliyunECSSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AliyunECSFilter
    search_fields = ['hostname', 'owner', 'project', 'private_ip', 'public_ip', 'account_name']
    ordering_fields = [
        'creation_time', 'instance_name', 'cpu', 'memory',
        'account_name', 'private_ip', 'public_ip', 'status'  # 加上这几个
    ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # 关键！直接用你自定义的分页响应
            return self.get_paginated_response(serializer.data)

        # 不分页情况（极少触发）
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "code": 200,
            "msg": "success",
            "data": {
                "page": 1,
                "total": queryset.count(),
                "pageSize": self.pagination_class.page_size,
                "data": serializer.data
            }
        })


    # ==================== 项目映射加载 ====================
    def _load_project_map(self):
        """加载 hostname → 项目信息映射（高效查询）"""
        project_map = {}
        try:
            for record in ProjectAliyunecs.objects.only('hostname', 'project', 'environment', 'owner').iterator():
                key = record.hostname.strip().lower()
                project_map[key] = {
                    'project': record.project,
                    'environment': record.environment,
                    'owner': record.owner,
                }
            logger.debug(f"加载 {len(project_map)} 条项目映射")
        except Exception as e:
            logger.error(f"项目映射加载失败: {e}")
        return project_map

    # ==================== 磁盘解析（v2 兼容） ====================
    def _parse_disk(self, disk_obj):
        """解析 v2 磁盘对象（Tea 风格）"""
        if not disk_obj:
            return {}
        # getattr 安全访问属性
        perf = getattr(disk_obj, 'performance_level', '') or ''
        perf_level = f"PL{perf[-1]}" if perf and len(perf) > 0 else "PL0"
        return {
            'device': getattr(disk_obj, 'device', '/dev/xvda'),
            'category': getattr(disk_obj, 'category', 'cloud_essd'),
            'performance_level': perf_level,
            'size': f"{getattr(disk_obj, 'size', 0)}GiB",
            'iops': getattr(disk_obj, 'iops', 0),
            'status': getattr(disk_obj, 'status', 'in_use').lower()
        }

    # ==================== 安全组提取（v2 兼容） ====================
    def _extract_security_group_ids(self, instance_obj):
        """提取 v2 实例的安全组ID列表"""
        sg_ids = []
        try:
            # v2: security_group_ids.security_group_id（Tea 列表）
            sg_container = getattr(instance_obj, 'security_group_ids', None)
            if sg_container and hasattr(sg_container, 'security_group_id'):
                sg_list = getattr(sg_container, 'security_group_id', [])
                if isinstance(sg_list, list):
                    sg_ids = [sg for sg in sg_list if sg]
                elif isinstance(sg_list, str) and sg_list:
                    sg_ids = [sg_list]

            # 备选: security_groups.security_group（对象列表）
            if not sg_ids:
                sg_container = getattr(instance_obj, 'security_groups', None)
                if sg_container and hasattr(sg_container, 'security_group'):
                    sg_objects = getattr(sg_container, 'security_group', [])
                    if isinstance(sg_objects, list):
                        sg_ids = [
                            getattr(sg, 'security_group_id', '') for sg in sg_objects
                            if getattr(sg, 'security_group_id', '')
                        ]
        except Exception as e:
            logger.warning(f"安全组提取失败: {e}")
        return sg_ids

    # ==================== 实例保存 ====================
    def _save_instance(self, account_name, region, instance_obj, project_map):
        """保存 v2 实例对象到数据库"""
        try:
            # 安全获取属性
            hostname = getattr(instance_obj, 'host_name', '').lower().strip()
            project_info = project_map.get(hostname, {})

            sg_ids = self._extract_security_group_ids(instance_obj)

            # v2 IP 处理（复杂嵌套）
            public_ips = []
            public_container = getattr(instance_obj, 'public_ip_address', None)
            if public_container and hasattr(public_container, 'ip_address'):
                ip_list = getattr(public_container, 'ip_address', [])
                if isinstance(ip_list, list):
                    public_ips = ip_list

            private_ips = []
            vpc_container = getattr(instance_obj, 'vpc_attributes', None)
            if vpc_container and hasattr(vpc_container, 'private_ip_address') and hasattr(vpc_container.private_ip_address, 'ip_address'):
                ip_list = getattr(vpc_container.private_ip_address, 'ip_address', [])
                if isinstance(ip_list, list):
                    private_ips = ip_list

            eip = ''
            eip_container = getattr(instance_obj, 'eip_address', None)
            if eip_container and hasattr(eip_container, 'ip_address'):
                eip = getattr(eip_container, 'ip_address', '')

            # 磁盘（v2 嵌套）
            system_disk = {}
            sys_disk_obj = getattr(instance_obj, 'system_disk', None)
            if sys_disk_obj:
                system_disk = self._parse_disk(sys_disk_obj)

            data_disks = []
            data_container = getattr(instance_obj, 'data_disks', None)
            if data_container and hasattr(data_container, 'data_disk'):
                disks = getattr(data_container, 'data_disk', [])
                if isinstance(disks, list):
                    data_disks = [self._parse_disk(d) for d in disks]

            defaults = {
                'account_name': account_name,  # 所属账号（关键）
                'instance_name': getattr(instance_obj, 'instance_name', ''),
                'hostname': hostname,
                'osname': getattr(instance_obj, 'osname', ''),
                'status': getattr(instance_obj, 'status', ''),
                'region': region,
                'zone': getattr(instance_obj, 'zone_id', ''),
                'public_ip': ','.join(public_ips),
                'private_ip': ','.join(private_ips),
                'eip': eip,
                'security_group_ids': sg_ids,
                'cpu': getattr(instance_obj, 'cpu', 0),
                'memory': getattr(instance_obj, 'memory', 0),
                'instance_type': getattr(instance_obj, 'instance_type', ''),
                'instance_family': getattr(instance_obj, 'instance_type_family', ''),
                'creation_time': convert_utc_to_shanghai(getattr(instance_obj, 'creation_time', None)),
                'expire_time': convert_utc_to_shanghai(getattr(instance_obj, 'expired_time', None)),
                'project': project_info.get('project'),
                'environment': project_info.get('environment'),
                'owner': project_info.get('owner'),
                'system_disk': system_disk,
                'data_disks': data_disks,
                'image_id': getattr(instance_obj, 'image_id', ''),
                'stopped_mode': getattr(instance_obj, 'stopped_mode', ''),
            }

            instance_id = getattr(instance_obj, 'instance_id', '')
            AliyunECS.objects.update_or_create(
                instance_id=instance_id,
                defaults=defaults
            )
            logger.debug(f"保存实例成功: {instance_id} ({account_name})")
        except Exception as e:
            logger.error(f"实例保存失败: {e}")

    # ==================== 磁盘同步（v2） ====================
    def _sync_disks(self, client, instance_id, region):
        """v2 详细磁盘同步"""
        try:
            runtime = RuntimeOptions()
            req = DescribeDisksRequest()
            req.instance_id = instance_id
            req.region_id = region
            resp = client.describe_disks_with_options(req, runtime)

            system_disk = {}
            data_disks = []

            disks_container = getattr(resp.body, 'disks', None)
            if disks_container and hasattr(disks_container, 'disk'):
                disks = getattr(disks_container, 'disk', [])
                if isinstance(disks, list):
                    for disk in disks:
                        parsed = self._parse_disk(disk)
                        disk_type = getattr(disk, 'type', '').lower()
                        if disk_type == 'system':
                            system_disk = parsed
                        else:
                            data_disks.append(parsed)

            AliyunECS.objects.filter(instance_id=instance_id).update(
                system_disk=system_disk,
                data_disks=data_disks
            )
            logger.debug(f"磁盘同步成功: {instance_id}")
        except Exception as e:
            logger.error(f"v2 磁盘同步失败 {instance_id}: {e}")

    # ==================== 单地域同步（v2） ====================
    def _sync_region(self, account, region, project_map):
        """v2 分页同步一个地域（已修复 MissingParameter）"""
        try:
            # 使用你的公共组件构建配置
            config = make_tea_config(account, region, 'ecs')
            client = EcsClient(config)
            runtime = RuntimeOptions()

            page = 1
            page_size = 100
            while True:
                req = DescribeInstancesRequest()
                req.page_number = page
                req.page_size = page_size
                req.additional_attributes = ['cloudDisk']

                # 关键修复：v2 SDK 必须显式设置 region_id
                req.region_id = region  # 加上这行，400 错误立刻消失！

                resp = client.describe_instances_with_options(req, runtime)

                # 提取实例列表（v2 结构）
                instances = []
                container = getattr(resp.body, 'instances', None)
                if container and hasattr(container, 'instance'):
                    raw = getattr(container, 'instance', [])
                    if isinstance(raw, list):
                        instances = raw
                    elif raw:
                        instances = [raw]

                logger.info(f"[{account['name']}-{region}] 第 {page} 页获取 {len(instances)} 台实例")

                for inst in instances:
                    self._save_instance(account['name'], region, inst, project_map)
                    inst_id = getattr(inst, 'instance_id', '')
                    if inst_id:
                        self._sync_disks(client, inst_id, region)

                if len(instances) < page_size:
                    break
                page += 1

        except Exception as e:
            logger.error(f"[{account['name']}-{region}] v2 同步失败: {e}")

    # ==================== 主同步入口 ====================
    def _sync_all_ecs(self):
        """完整 v2 同步流程"""
        logger.info("开始 v2 阿里云ECS同步")
        project_map = self._load_project_map()
        accounts = get_aliyun_accounts()

        if not accounts:
            logger.warning("未检测到阿里云账号配置")
            return

        for account in accounts:
            logger.info(f"同步账号: {account['name']}，地域: {account['regions']}")
            for region in account['regions']:
                for attempt in range(3):  # 重试3次
                    try:
                        self._sync_region(account, region, project_map)
                        break
                    except Exception as e:
                        if attempt == 2:
                            logger.error(f"重试失败 [{account['name']}-{region}]: {e}")
                        time.sleep(1)  # 等待重试

        logger.info("v2 ECS同步完成")

    # ==================== 对外接口 ====================
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """一键同步接口（前端按钮调用）"""
        def run():
            try:
                self._sync_all_ecs()
            except Exception as e:
                logger.error(f"v2 同步线程异常: {e}", exc_info=True)

        threading.Thread(target=run, daemon=True).start()
        return Response({
            "code": 200,
            "message": "v2 ECS同步已启动（预计3-10分钟），请刷新查看"
        }, status=status.HTTP_202_ACCEPTED)

class ProjectAliyunecsViewSet(viewsets.ModelViewSet):
    queryset = ProjectAliyunecs.objects.all()
    serializer_class = ProjectAliyunecsSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'hostname': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
        'department': ['exact', 'icontains'],
    }
    search_fields = ['hostname', 'project', 'owner', 'department', 'business_unit', 'notes']
    ordering_fields = ['hostname', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'hostname']


# -------------------- 阿里云域名 & DNS --------------------
def check_domain_permissions(account):
    """检查域名服务权限，返回 True/False，绝不抛出异常"""
    try:
        config = make_tea_config(account, 'cn-hangzhou', 'domain')
        client = DomainClient(config)
        req = QueryDomainListRequest()
        req.page_size = 1
        req.page_num = 1  # ✅ 修复：添加缺失的必需参数
        runtime = RuntimeOptions()

        # 实际调用API验证权限
        resp = client.query_domain_list_with_options(req, runtime)
        logger.info(f"✅ 账号 {account['name']} 权限检查通过")
        return True

    except ClientException as e:
        if e.code == 'Forbidden.RAM':
            logger.error(f"❌ 账号 {account['name']} 缺少域名服务权限: {e.message}")
            logger.error(f"   请前往RAM控制台为 {account['name']} 添加策略: domain:QueryDomainList")
        elif e.code == 'MissingPageNum':
            logger.error(f"❌ 账号 {account['name']} 权限检查参数错误（不应发生）: {e}")
        else:
            logger.warning(f"⚠️ 账号 {account['name']} 权限检查失败: {e.code} - {e.message}")
        return False

    except Exception as e:
        logger.error(f"❌ 账号 {account['name']} 权限检查异常: {e}", exc_info=True)
        return False

class AliyunDomainViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AliyunDomain.objects.all()
    serializer_class = AliyunDomainSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['domain_name', 'account_name']
    ordering = ['-expiration_date']

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """同步域名列表"""
        try:
            with transaction.atomic():
                domain_count = self._sync_all_domains()

            logger.info(f'域名同步成功，共 {domain_count} 个')
            return Response({
                'status': 'success',
                'message': f'成功同步 {domain_count} 个域名',
                'count': domain_count
            })
        except Exception as e:
            logger.exception("阿里云域名同步失败")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _sync_all_domains(self):
        """同步所有账号下的域名，智能跳过无权限账号"""
        accounts = get_aliyun_accounts()
        if not accounts:
            raise ValueError("未在 aliyun/conf/aliyun.cnf 中配置任何阿里云账号")

        # ✅ 改进：安全地检查每个账号，不抛出异常
        valid_accounts = []
        for acc in accounts:
            try:
                if check_domain_permissions(acc):
                    valid_accounts.append(acc)
                else:
                    logger.warning(f"跳过账号 {acc['name']}：权限不足")
            except Exception as e:
                logger.warning(f"检查账号 {acc['name']} 时出错，跳过: {e}")
                continue

        if not valid_accounts:
            raise Exception("所有账号均无域名服务访问权限！请检查RAM策略配置")

        logger.info(f"开始同步 {len(valid_accounts)} 个有效账号（共配置 {len(accounts)} 个）")

        total = 0
        runtime = RuntimeOptions(read_timeout=30000, connect_timeout=30000)

        for acc in valid_accounts:
            try:
                logger.info(f"处理账号: {acc['name']}")
                config = make_tea_config(acc, 'cn-hangzhou', 'domain')
                client = DomainClient(config)

                req = QueryDomainListRequest()
                req.page_size = 100
                page = 1

                while True:
                    req.page_num = page
                    resp = client.query_domain_list_with_options(req, runtime)
                    domains = resp.body.data.domain or []

                    if not domains:
                        break

                    for d in domains:
                        try:
                            self._save_domain(client, d, acc['name'], runtime)
                            total += 1
                        except Exception as e:
                            logger.warning(f"同步域名 {d.domain_name} 失败: {e}")
                            continue

                    if len(domains) < 100:
                        break
                    page += 1

            except Exception as e:
                logger.error(f"账号 {acc['name']} 同步失败: {e}", exc_info=True)
                continue  # 继续下一个账号

        logger.info(f"域名批量同步完成，总计成功: {total}")
        return total

    def _save_domain(self, client, d, account_name, runtime):
        """保存单个域名详细信息"""
        try:
            # 获取域名详情
            detail_req = QueryDomainByDomainNameRequest()
            detail_req.domain_name = d.domain_name
            detail_resp = client.query_domain_by_domain_name_with_options(detail_req, runtime)

            # ✅ 核心修复：domain_status 是字符串，不是列表
            # 根据阿里云官方 API，domain_status 直接返回字符串状态码
            defaults = {
                'account_name': account_name,
                'registration_date': convert_utc_to_shanghai(d.registration_date),
                'expiration_date': convert_utc_to_shanghai(d.expiration_date),
                'domain_status': d.domain_status or 'unknown',  # ✅ 修复：直接字符串
                'dns_server': ','.join(detail_resp.body.dns_list.dns or []),
                'registrant_type': detail_resp.body.registrant_type or '',
                'registrant_organization': detail_resp.body.registrant_organization or '',
                'registrant': detail_resp.body.registrant_name or '',
                'email': detail_resp.body.email or '',
            }

            domain_obj, created = AliyunDomain.objects.update_or_create(
                domain_name=d.domain_name,
                defaults=defaults
            )

            action = "创建" if created else "更新"
            logger.debug(f"{action}域名: {d.domain_name}")

        except Exception as e:
            logger.error(f"保存域名 {d.domain_name} 失败: {e}", exc_info=True)
            raise

class AliyunDNSRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AliyunDNSRecord.objects.select_related('domain').all()
    serializer_class = AliyunDNSRecordSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'environment', 'owner', 'type', 'status']
    search_fields = ['complete_domain', 'value', 'project', 'owner', 'remark']
    ordering_fields = ['complete_domain', 'update_timestamp']
    ordering = ['complete_domain']

    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request):
        """全量同步：域名 + DNS记录 + 项目信息"""
        try:
            with transaction.atomic():
                logger.info("开始全量同步流程...")
                domain_count = self._sync_all_domains()
                logger.info(f"域名同步完成: {domain_count} 个")

                record_count = self._sync_all_dns_records()
                logger.info(f"DNS记录同步完成: {record_count} 条")

                project_count = self._sync_project_info()
                logger.info(f"项目信息同步完成: {project_count} 条")

            return Response({
                'status': 'success',
                'message': '同步完成',
                'data': {
                    'domains_synced': domain_count,
                    'records_synced': record_count,
                    'project_info_updated': project_count
                }
            })
        except Exception as e:
            logger.exception("阿里云DNS同步失败")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _sync_all_domains(self):
        """复用 AliyunDomainViewSet 的域名同步逻辑"""
        viewset = AliyunDomainViewSet()
        return viewset._sync_all_domains()

    def _sync_all_dns_records(self):
        """同步所有账号下所有域名的 DNS 记录"""
        accounts = get_aliyun_accounts()
        if not accounts:
            raise ValueError("未配置阿里云账号")

        # 预加载项目映射，大幅提升性能
        proj_map = {
            p.complete_domain.lower(): p
            for p in ProjectAliyunDomain.objects.all()
        }
        logger.info(f"预加载项目映射: {len(proj_map)} 条")

        total_records = 0
        runtime = RuntimeOptions(read_timeout=30000, connect_timeout=30000)

        for acc in accounts:
            logger.info(f"开始同步账号 {acc['name']} 的DNS记录")
            config = make_tea_config(acc, 'cn-hangzhou', 'alidns')
            client = DnsClient(config)

            # 获取该账号下的所有域名
            domains = AliyunDomain.objects.filter(account_name=acc['name'])
            if not domains:
                logger.warning(f"账号 {acc['name']} 下无域名，跳过")
                continue

            for domain in domains:
                try:
                    records_synced = self._sync_domain_records(client, domain, proj_map, runtime)
                    total_records += records_synced
                except Exception as e:
                    logger.warning(f"同步域名 {domain.domain_name} 的记录失败: {e}")
                    continue

        logger.info(f"所有账号DNS记录同步完成，总计: {total_records}")
        return total_records

    def _sync_domain_records(self, client, domain, proj_map, runtime):
        """同步单个域名的所有记录"""
        req = DescribeDomainRecordsRequest()
        req.domain_name = domain.domain_name
        req.page_size = 500
        page = 1
        count = 0

        while True:
            req.page_number = page
            resp = client.describe_domain_records_with_options(req, runtime)
            records = resp.body.domain_records.record or []

            if not records:
                break

            for r in records:
                try:
                    # 计算完整域名
                    full_domain = (
                        domain.domain_name.lower()
                        if r.rr == '@'
                        else f"{r.rr}.{domain.domain_name}".lower()
                    )
                    proj = proj_map.get(full_domain)

                    # 防御性编程：处理所有可能为 None 的字段
                    defaults = {
                        'domain': domain,
                        'domain_name': domain.domain_name,
                        'rr': r.rr or '',
                        'type': (r.type or '').upper(),
                        'value': r.value or '',
                        'ttl': r.ttl or 600,
                        'status': r.status or 'ENABLE',
                        'line': r.line or 'default',
                        'locked': bool(getattr(r, 'locked', False)),
                        'weight': getattr(r, 'weight', None),
                        'remark': getattr(r, 'remark', ''),
                        'project': getattr(proj, 'project', None),
                        'environment': getattr(proj, 'environment', None),
                        'owner': getattr(proj, 'owner', None),
                        'create_timestamp': convert_utc_to_shanghai(getattr(r, 'create_timestamp', None)),
                        'update_timestamp': convert_utc_to_shanghai(getattr(r, 'update_timestamp', None)),
                    }

                    # 自动计算 complete_domain
                    record_obj, created = AliyunDNSRecord.objects.update_or_create(
                        record_id=r.record_id,
                        defaults=defaults
                    )

                    # 触发 save 方法计算 complete_domain
                    if created:
                        record_obj.save()

                    count += 1
                except Exception as e:
                    logger.warning(f"保存记录 {r.record_id} 失败: {e}")
                    continue

            if len(records) < 500:
                break
            page += 1

        logger.debug(f"域名 {domain.domain_name} 同步记录: {count} 条")
        return count

    def _sync_project_info(self):
        """将 ProjectAliyunDomain 项目信息同步到 DNS 记录"""
        updated = 0

        # 批量更新，减少数据库操作
        for proj in ProjectAliyunDomain.objects.all():
            cnt = AliyunDNSRecord.objects.filter(
                complete_domain__iexact=proj.complete_domain
            ).update(
                project=proj.project,
                environment=proj.environment,
                owner=proj.owner,
                is_auto=False  # 标记为手动同步的项目信息
            )
            if cnt > 0:
                logger.debug(f"项目 {proj.project} 更新 {cnt} 条记录")
            updated += cnt

        logger.info(f"项目信息同步完成，总计更新 {updated} 条DNS记录")
        return updated

class ProjectAliyunDomainViewSet(viewsets.ModelViewSet):
    queryset = ProjectAliyunDomain.objects.all()
    serializer_class = ProjectAliyunDomainSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'complete_domain': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
        'type': ['exact'],
    }
    search_fields = ['complete_domain', 'rr', 'project', 'owner', 'description']
    ordering_fields = ['complete_domain', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'complete_domain']

# -------------------- 阿里云 RDS --------------------

class AliyunRDSViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AliyunRDS.objects.all()
    serializer_class = AliyunRDSSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region_id', 'engine', 'instance_type', 'pay_type', 'status', 'account_name']
    search_fields = ['instance_id', 'instance_name', 'connection_string']
    ordering = ['-updated_at']

    # 关键：重写 retrieve，让详情接口也返回 { code: 200, data: ... }
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'msg': 'success',
            'data': serializer.data
        })

    def _create_client(self, account: dict, region: str) -> Optional[Rds20140815Client]:
        """统一创建客户端（使用公共组件）"""
        try:
            config = make_tea_config(account, region, 'rds')
            # 关键：官方要求统一入口必须传 region_id
            config.region_id = region
            config.connect_timeout = 5000
            config.read_timeout = 10000
            return Rds20140815Client(config)
        except Exception as e:
            logger.error(f"创建 RDS 客户端失败 [{account['name']}/{region}]: {e}")
            return None

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """全量同步 RDS 实例（官方推荐两步法）"""
        logger.info("=== 开始同步阿里云 RDS 实例 ===")
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置阿里云账号'}, status=400)

        # 加载 RDS 项目映射（根据实例名称）
        rds_project_map = {}
        try:
            for record in ProjectAliyunRDS.objects.only('instance_name', 'project', 'environment', 'owner', 'description').iterator():
                key = record.instance_name.strip().lower()
                rds_project_map[key] = {
                    'project': record.project,
                    'environment': record.environment,
                    'owner': record.owner,
                    'description': record.description,
                }
            logger.debug(f"加载 {len(rds_project_map)} 条RDS项目映射")
        except Exception as e:
            logger.error(f"RDS项目映射加载失败: {e}")

        total_synced = 0
        failed_regions = []
        account_stats = []

        for account in accounts:
            acc_name = account['name']
            acc_count = 0
            logger.info(f"正在处理账号: {acc_name}（共 {len(account['regions'])} 个地域）")

            for region in account['regions']:
                client = self._create_client(account, region)
                if not client:
                    failed_regions.append(f"{acc_name}/{region}")
                    continue

                runtime = util_models.RuntimeOptions()
                runtime.autoretry = True
                runtime.max_attempts = 3

                page = 1
                while True:
                    req = rds_models.DescribeDBInstancesRequest(
                        page_size=100,
                        page_number=page,
                        # 必须显式传 region_id（双保险）
                        region_id=region
                    )

                    try:
                        resp = client.describe_dbinstances_with_options(req, runtime)
                    except Exception as e:
                        logger.error(f"[{acc_name}/{region}] DescribeDBInstances 失败: {e}")
                        failed_regions.append(f"{acc_name}/{region}")
                        break

                    if not resp or not resp.body or not resp.body.items:
                        break

                    instances = resp.body.items.dbinstance or []
                    if not instances:
                        break

                    for inst in instances:
                        instance_id = inst.dbinstance_id  # 正确字段名

                        # 第二步：获取完整详情
                        detail_req = rds_models.DescribeDBInstanceAttributeRequest(
                            dbinstance_id=instance_id,
                        )
                        try:
                            detail_resp = client.describe_dbinstance_attribute_with_options(detail_req, runtime)
                        except Exception as e:
                            logger.warning(f"获取实例详情失败 {instance_id}: {e}")
                            continue

                        if not detail_resp or not detail_resp.body or not detail_resp.body.items:
                            continue

                        detail = detail_resp.body.items.dbinstance_attribute[0]

                        # 处理只读实例（终极正确版）
                        read_only_instances = []
                        ro_ids = []

                        # 正确获取只读实例 ID 列表
                        if hasattr(detail, 'read_only_dbinstance_ids') and detail.read_only_dbinstance_ids:
                            ro_ids = getattr(detail.read_only_dbinstance_ids, 'read_only_dbinstance_id', []) or []

                        for ro_id in ro_ids:
                            if not ro_id:
                                continue
                            try:
                                ro_req = rds_models.DescribeDBInstanceAttributeRequest(dbinstance_id=ro_id)
                                ro_resp = client.describe_dbinstance_attribute_with_options(ro_req, runtime)
                                if ro_resp and ro_resp.body and ro_resp.body.items and ro_resp.body.items.dbinstance_attribute:
                                    ro = ro_resp.body.items.dbinstance_attribute[0]
                                    read_only_instances.append({
                                        'id': ro.dbinstance_id,
                                        'name': getattr(ro, 'dbinstance_description', 'Unnamed'),
                                        'status': ro.dbinstance_status,
                                        'class': ro.dbinstance_class,
                                        'engine': ro.engine,
                                        'engine_version': ro.engine_version,
                                        'zone_id': getattr(ro, 'zone_id', ''),
                                    })
                            except Exception as e:
                                logger.debug(f"只读实例 {ro_id} 查询失败（忽略）: {e}")

                        # 标签
                        tags = {}
                        if hasattr(detail, 'tags') and detail.tags and hasattr(detail.tags, 'tag'):
                            for t in detail.tags.tag:
                                tags[t.key] = t.value

                        defaults = {
                            'instance_name': getattr(detail, 'dbinstance_description', ''),
                            'account_name': acc_name,
                            'region_id': region,
                            'engine': detail.engine,
                            'engine_version': detail.engine_version,
                            'instance_type': detail.dbinstance_type,
                            'instance_class': detail.dbinstance_class,
                            'storage': detail.dbinstance_storage,
                            'memory': detail.dbinstance_memory,
                            'cpu': detail.dbinstance_cpu,
                            'connection_string': detail.connection_string,
                            'port': detail.port,
                            'vpc_id': getattr(detail, 'vpc_id', ''),
                            'vswitch_id': getattr(detail, 'vswitch_id', ''),
                            'security_ips': getattr(detail, 'security_ip_list', ''),
                            'pay_type': detail.pay_type,
                            'creation_time': convert_utc_to_shanghai(getattr(detail, 'creation_time', None)),
                            'expire_time': convert_utc_to_shanghai(getattr(detail, 'expire_time', None)),
                            'status': detail.dbinstance_status,
                            'zone_id': getattr(detail, 'zone_id', ''),
                            'read_only_instances': read_only_instances,
                            'tags': tags,
                            'updated_at': django_timezone.now(),
                        }

                        # 应用项目映射（根据实例名称匹配）
                        instance_name_lower = defaults['instance_name'].strip().lower()
                        project_info = rds_project_map.get(instance_name_lower, {})
                        if project_info:
                            defaults['project'] = project_info.get('project')
                            defaults['environment'] = project_info.get('environment')
                            defaults['owner'] = project_info.get('owner')
                            defaults['description'] = project_info.get('description')

                        try:
                            with transaction.atomic():
                                AliyunRDS.objects.update_or_create(
                                    instance_id=detail.dbinstance_id,
                                    defaults=defaults
                                )
                            total_synced += 1
                            acc_count += 1
                        except Exception as db_e:
                            logger.error(f"保存实例 {instance_id} 失败: {db_e}")

                    if len(instances) < 100:
                        break
                    page += 1
                    time.sleep(0.1)  # 简单防爆接口

            account_stats.append({'account': acc_name, 'count': acc_count})

        logger.info(f"=== RDS 同步完成，共同步 {total_synced} 条 ===")
        if failed_regions:
            logger.warning(f"失败地域: {', '.join(failed_regions)}")

        return Response({
            'status': 'success',
            'total': total_synced,
            'accounts': account_stats,
            'failed_regions': failed_regions or None,
            'synced_at': django_timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })


class ProjectAliyunRDSViewSet(viewsets.ModelViewSet):
    queryset = ProjectAliyunRDS.objects.all()
    serializer_class = ProjectAliyunRDSSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'instance_name': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
        'department': ['exact', 'icontains'],
    }
    search_fields = ['instance_name', 'project', 'owner', 'department', 'business_unit', 'description', 'notes']
    ordering_fields = ['instance_name', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'instance_name']


# -------------------- 阿里云 EIP --------------------
class AliyunEIPViewSet(viewsets.ReadOnlyModelViewSet, SyncActionMixin):
    queryset = AliyunEIP.objects.all()
    serializer_class = AliyunEIPSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region_id', 'status', 'account_name', 'internet_charge_type']
    search_fields = ['allocation_id', 'name', 'ip_address', 'instance_id']
    ordering = ['-updated_at']

    @action(detail=False, methods=['post'])
    def sync(self, request):
        logger.info('开始同步 EIP')
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置账号'}, status=400)
        total = 0
        for acc in accounts:
            for region in acc['regions']:
                cfg = make_tea_config(acc, region, 'vpc')
                client = VpcClient(cfg)
                req = DescribeEipAddressesRequest()
                req.page_size = 50
                runtime = RuntimeOptions()
                page = 1
                while True:
                    req.page_number = page
                    resp = client.describe_eip_addresses_with_options(req, runtime)
                    eips = resp.body.eip_addresses.eip_address
                    if not eips:
                        break
                    for eip in eips:
                        defaults = {
                            'name': eip.name,
                            'account_name': acc['name'],
                            'region_id': region,
                            'status': eip.status,
                            'instance_id': eip.instance_id,
                            'instance_type': eip.instance_type,
                            'bandwidth': str(eip.bandwidth),
                            'internet_charge_type': eip.internet_charge_type,
                            'ip_address': eip.ip_address,
                            'allocation_time': eip.allocation_time,
                            'expired_time': eip.expired_time or None,
                            'tags': {t.key: t.value for t in (eip.tags.tag or [])} if eip.tags else {},
                        }
                        AliyunEIP.objects.update_or_create(allocation_id=eip.allocation_id, defaults=defaults)
                        total += 1
                    if len(eips) < 50:
                        break
                    page += 1
        logger.info(f'EIP 同步完成，共 {total} 条')
        return Response({'status': 'success', 'count': total})


# -------------------- 阿里云 WAF --------------------
class AliyunWAFViewSet(viewsets.ReadOnlyModelViewSet, SyncActionMixin):
    queryset = AliyunWAF.objects.all()
    serializer_class = AliyunWAFSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'account_name']
    search_fields = ['instance_id', 'instance_name']
    ordering = ['-updated_at']

    # 关键：重写 retrieve，让详情接口也返回 { code: 200, data: ... }
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'msg': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def sync(self, request):
        logger.info('=== 开始同步阿里云 WAF 实例 ===')
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置阿里云账号'}, status=400)

        total_synced = 0
        failed_accounts = []

        region = 'cn-hangzhou'

        for acc in accounts:
            acc_name = acc['name']
            try:
                cfg = make_tea_config(acc, region, 'waf-openapi')
                client = WafClient(cfg)
                runtime = RuntimeOptions()
                runtime.autoretry = True
                runtime.max_attempts = 3

                # 一行搞定所有异常！
                resp = safe_api_call(
                    lambda: client.describe_instance_with_options(DescribeInstanceRequest(), runtime)
                )

                if not resp or not resp.body:
                    logger.info(f"账号 [{acc_name}] 无 WAF 实例或无权限，已自动跳过")
                    failed_accounts.append(acc_name)
                    continue

                ins = resp.body

                # 时间字段统一处理（你已有的函数）
                defaults = {
                    'region_id': region,
                    'account_name': acc_name,
                    'status': getattr(ins, 'status', 1),
                    'pay_type': getattr(ins, 'pay_type', 'PREPAY'),
                    'edition': getattr(ins, 'edition', ''),
                    'start_time': convert_utc_to_shanghai(ins.start_time),
                    'end_time': convert_utc_to_shanghai(ins.end_time),
                    'details': ins.details.to_map() if hasattr(ins, 'details') and ins.details else {},
                    'all_details': ins.to_map(),
                    'tamperproof': bool(getattr(ins.details, 'tamperproof', False)) if hasattr(ins, 'details') else False,
                    'bot': bool(ins.details.bot) if ins.details else False,
                    'custom_rule': bool(ins.details.custom_rule) if ins.details else False,
                    'ip_blacklist': bool(ins.details.ip_blacklist) if ins.details else False,
                    'dlp': bool(ins.details.dlp) if ins.details else False,
                    'anti_scan': bool(ins.details.anti_scan) if ins.details else False,
                    'log_service': bool(ins.details.log_service) if ins.details else False,
                    'updated_at': convert_utc_to_shanghai(django_timezone.now())
                }

                AliyunWAF.objects.update_or_create(
                    instance_id=ins.instance_id,
                    defaults=defaults
                )
                total_synced += 1

            except Exception as e:
                logger.error(f"账号 [{acc_name}] 同步时发生未捕获异常: {e}", exc_info=True)
                failed_accounts.append(acc_name)

        logger.info(f"WAF 同步完成，成功 {total_synced} 条，跳过账号: {failed_accounts}")
        return Response({
            'status': 'success',
            'count': total_synced,
            'failed_accounts': failed_accounts or None,
        })

# ====================== SNAT 网关 ======================

def check_vpc_permissions(account, region):
    """
    检查VPC权限（智能区分错误类型）
    - 参数错误说明API可达，权限正常
    - Forbidden.RAM 说明真实无权限
    返回: True/False
    """
    try:
        config = make_tea_config(account, region, 'vpc')
        client = VpcClient(config)
        req = DescribeNatGatewaysRequest()
        req.region_id = region
        req.page_size = 10  # ✅ 使用小值进行权限验证
        runtime = RuntimeOptions()

        client.describe_nat_gateways_with_options(req, runtime)
        logger.debug(f"✅ 账号 {account['name']} 在 {region} 区域权限正常")
        return True

    except ClientException as e:
        # ✅ 参数错误 = API可达 = 权限正常
        if e.code == 'DESCRIBE_NATGATEWAYS_PARAM_INVALID':
            logger.debug(f"✅ 账号 {account['name']} 在 {region} 区域权限正常（参数校验通过）")
            return True

        # ❌ RAM权限错误
        elif e.code == 'Forbidden.RAM':
            logger.warning(f"❌ 账号 {account['name']} 在 {region} 区域无VPC权限: {e.message}")
            return False

        # ❌ 其他参数错误（可能PageSize无效）
        elif e.code == 'InvalidParameter' and 'PageSize' in e.message:
            logger.debug(f"✅ 账号 {account['name']} 在 {region} 区域权限正常（PageSize校验通过）")
            return True

        else:
            logger.warning(f"⚠️ 账号 {account['name']} 在 {region} 区域检查失败: {e.code}")
            return False

    except Exception as e:
        logger.error(f"❌ VPC权限检查异常 {account['name']}-{region}: {e}")
        return False

class AliyunSNATEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AliyunSNATEntry.objects.all()
    serializer_class = AliyunSNATEntrySerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region_id', 'nat_gateway_id', 'status', 'account_name']
    search_fields = ['hostname', 'source_cidr', 'snat_ip', 'snat_entry_name']
    ordering = ['-updated_at']

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """同步SNAT记录（先查NAT网关，再查SNAT条目）"""
        logger.info('=' * 60)
        logger.info('🚀 开始同步 SNAT 记录')

        accounts = get_aliyun_accounts()
        if not accounts:
            logger.error("未配置阿里云账号")
            return Response({'status': 'error', 'message': '未配置阿里云账号'}, status=400)

        total = 0
        success_accounts = 0
        failed_accounts = []
        account_results = []

        for acc in accounts:
            account_total = 0
            account_regions_success = 0

            logger.info(f"▶️ 处理账号: {acc['name']}")

            for region in acc['regions']:
                if not check_vpc_permissions(acc, region):
                    logger.info(f"  ⏭️  跳过区域 {region}（权限不足）")
                    continue

                try:
                    region_total = self._sync_region_snat(acc, region)
                    if region_total > 0:
                        account_total += region_total
                        account_regions_success += 1
                        logger.info(f"  ✅ 区域 {region} 同步完成: {region_total} 条")

                except Exception as e:
                    logger.error(f"  ❌ 区域 {region} 同步异常: {e}", exc_info=True)
                    continue

            if account_total > 0:
                success_accounts += 1
                account_results.append({
                    'account': acc['name'],
                    'status': 'success',
                    'count': account_total,
                    'regions_successful': account_regions_success
                })
                logger.info(f"✅ 账号 {acc['name']} 同步成功: {account_total} 条")
            else:
                failed_accounts.append(acc['name'])
                account_results.append({
                    'account': acc['name'],
                    'status': 'skipped',
                    'reason': '无有效数据或无权限'
                })
                logger.warning(f"⚠️  账号 {acc['name']} 无有效同步数据")

        result_msg = f"SNAT同步完成: 成功 {success_accounts} 个账号, 总计 {total} 条记录"
        if failed_accounts:
            result_msg += f" | 失败/跳过账号: {', '.join(failed_accounts)}"

        logger.info('=' * 60)
        logger.info(f"🎉 {result_msg}")

        return Response({
            'status': 'success',
            'count': total,
            'accounts_successful': success_accounts,
            'accounts_failed': failed_accounts,
            'details': account_results,
            'message': result_msg
        })

    def _sync_region_snat(self, account, region):
        """同步单个区域的SNAT记录"""
        cfg = make_tea_config(account, region, 'vpc')
        client = VpcClient(cfg)
        runtime = RuntimeOptions(read_timeout=30000, connect_timeout=30000)
        region_total = 0

        # 查询 NAT 网关列表
        nat_gateways = self._get_nat_gateways(client, region, runtime)

        if not nat_gateways:
            logger.info(f"    区域 {region} 无NAT网关，跳过")
            return 0

        logger.info(f"    区域 {region} 发现 {len(nat_gateways)} 个NAT网关")

        # 遍历每个 NAT 网关查询 SNAT 条目
        for gw in nat_gateways:
            nat_gateway_id = gw['nat_gateway_id']
            snat_table_id = gw['snat_table_id']

            if not snat_table_id:
                logger.warning(f"      网关 {nat_gateway_id} 无SnatTableId，跳过")
                continue

            logger.debug(f"      处理网关 {nat_gateway_id} (SnatTableId: {snat_table_id})")

            req = DescribeSnatTableEntriesRequest()
            req.region_id = region
            req.nat_gateway_id = nat_gateway_id
            req.page_size = 50  # ✅ 保持50，VPC API支持
            page = 1
            gateway_total = 0

            while True:
                req.page_number = page
                resp = client.describe_snat_table_entries_with_options(req, runtime)
                entries = getattr(resp.body.snat_table_entries, 'snat_table_entry', [])

                if not entries:
                    break

                for entry in entries:
                    try:
                        # 主机名匹配逻辑
                        hostnames = []
                        source_cidr = getattr(entry, 'source_cidr', '') or ''

                        if source_cidr and '/' in source_cidr:
                            # 去掉 /32, /24 等后缀，保留 IP 部分
                            ip_part = source_cidr.split('/')[0]

                            # 直接查询 ECS 表中 private_ip 等于该 IP 的记录
                            ecs_list = AliyunECS.objects.filter(
                                private_ip=ip_part  # 精确匹配
                            ).values_list('hostname', flat=True).distinct()
                            hostnames = [h for h in ecs_list if h]

                        defaults = {
                            'snat_table_id': snat_table_id,
                            'nat_gateway_id': entry.nat_gateway_id,
                            'snat_entry_name': getattr(entry, 'snat_entry_name', '') or '',
                            'source_cidr': source_cidr,
                            'snat_ip': entry.snat_ip,
                            'source_vswitch_id': getattr(entry, 'source_vswitch_id', '') or '',
                            'network_interface_id': getattr(entry, 'network_interface_id', '') or '',
                            'status': entry.status,
                            'region_id': region,
                            'account_name': account['name'],
                            'eip_affinity': getattr(entry, 'eip_affinity', '') or '',
                            'hostname': ', '.join(hostnames) if hostnames else None,
                            'updated_at': convert_utc_to_shanghai(getattr(entry, 'updated_at', None)),
                        }

                        AliyunSNATEntry.objects.update_or_create(
                            snat_entry_id=entry.snat_entry_id,
                            defaults=defaults
                        )
                        gateway_total += 1
                        region_total += 1

                    except Exception as e:
                        logger.warning(f"        记录 {entry.snat_entry_id} 保存失败: {e}")
                        continue

                if len(entries) < 50:
                    break
                page += 1

            logger.debug(f"      网关 {nat_gateway_id} 同步: {gateway_total} 条")

        return region_total

    def _get_nat_gateways(self, client, region, runtime):
        """获取 NAT 网关列表（修复分页参数）"""
        from alibabacloud_vpc20160428.models import DescribeNatGatewaysRequest

        req = DescribeNatGatewaysRequest()
        req.region_id = region
        # ✅ VPC API PageSize 限制为 1-50
        req.page_size = 50
        page = 1
        nat_gateways = []

        while True:
            req.page_number = page
            resp = client.describe_nat_gateways_with_options(req, runtime)
            gateways = getattr(resp.body.nat_gateways, 'nat_gateway', [])

            if not gateways:
                break

            for gw in gateways:
                # 提取 SnatTableIds
                snat_table_id = ''
                if hasattr(gw, 'snat_table_ids') and hasattr(gw.snat_table_ids, 'snat_table_id'):
                    snat_table_ids = gw.snat_table_ids.snat_table_id
                    if snat_table_ids and len(snat_table_ids) > 0:
                        snat_table_id = snat_table_ids[0]

                nat_gateways.append({
                    'nat_gateway_id': gw.nat_gateway_id,
                    'snat_table_id': snat_table_id,
                    'name': getattr(gw, 'name', ''),
                    'status': getattr(gw, 'status', ''),
                })

            if len(gateways) < 50:
                break
            page += 1

        return nat_gateways



# -------------------- 阿里云 NAS --------------------
class AliyunNASViewSet(viewsets.ReadOnlyModelViewSet, SyncActionMixin):
    queryset = AliyunNAS.objects.all()
    serializer_class = AliyunNASSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region_id', 'protocol_type', 'storage_type', 'status', 'account_name']
    search_fields = ['file_system_id', 'file_system_name', 'description']
    ordering = ['-updated_at']

    # 关键：重写 retrieve，让详情接口也返回 { code: 200, data: ... }
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'msg': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def sync(self, request):
        logger.info('=== 开始同步阿里云 NAS ===')
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置账号'}, status=400)

        # 加载 NAS 项目映射（根据文件系统名称）
        nas_project_map = {}
        try:
            for record in ProjectAliyunNAS.objects.only('file_system_name', 'project', 'environment', 'owner', 'description').iterator():
                key = record.file_system_name.strip().lower()
                nas_project_map[key] = {
                    'project': record.project,
                    'environment': record.environment,
                    'owner': record.owner,
                    'remark': record.description,
                }
            logger.debug(f"加载 {len(nas_project_map)} 条NAS项目映射")
        except Exception as e:
            logger.error(f"NAS项目映射加载失败: {e}")

        total_synced = 0
        failed_accounts = []


        for acc in accounts:
            acc_name = acc['name']
            try:
                for region in acc['regions']:
                    cfg = make_tea_config(acc, region, 'nas')
                    client = NasClient(cfg)
                    runtime = RuntimeOptions()

                    page = 1
                    while True:
                        req = DescribeFileSystemsRequest()
                        req.page_size = 100
                        req.page_number = page

                        resp = safe_api_call(
                            lambda: client.describe_file_systems_with_options(req, runtime)
                        )

                        if not resp or not resp.body or not resp.body.file_systems:
                            break

                        fss = resp.body.file_systems.file_system or []
                        if not fss:
                            break

                        for fs in fss:
                            mt = (fs.mount_targets.mount_target[
                                      0] if fs.mount_targets and fs.mount_targets.mount_target else None)
                            defaults = {
                                'file_system_name': fs.description or fs.file_system_id,
                                'account_name': acc_name,
                                'region_id': region,
                                'description': fs.description or '',
                                'protocol_type': fs.protocol_type or '',
                                'storage_type': fs.storage_type or '',
                                'metered_size': getattr(fs, 'metered_size', 0),
                                'capacity': getattr(fs, 'capacity', 0),
                                'bandwidth': getattr(fs, 'bandwidth', 0) or 0,
                                'zone_id': fs.zone_id or '',
                                'vpc_id': getattr(mt, 'vpc_id', '') if mt else '',
                                'vswitch_id': getattr(mt, 'vsw_id', '') if mt else '',
                                'create_time': convert_utc_to_shanghai(fs.create_time),
                                'mount_target_count': len(fs.mount_targets.mount_target or []),
                                'status': fs.status or '',
                                'pay_type': fs.charge_type or '',
                                'tags': {t.key: t.value for t in (fs.tags.tag or [])} if hasattr(fs,
                                                                                                 'tags') and fs.tags else {},
                                'updated_at': django_timezone.now(),
                            }

                            # 应用项目映射（根据文件系统名称匹配）
                            fs_name_lower = defaults['file_system_name'].strip().lower()
                            project_info = nas_project_map.get(fs_name_lower, {})
                            if project_info:
                                defaults['project'] = project_info.get('project')
                                defaults['environment'] = project_info.get('environment')
                                defaults['owner'] = project_info.get('owner')
                                defaults['remark'] = project_info.get('remark')

                            AliyunNAS.objects.update_or_create(
                                file_system_id=fs.file_system_id,
                                defaults=defaults
                            )
                            total_synced += 1


                        if len(fss) < 100:
                            break
                        page += 1

            except Exception as e:
                logger.error(f"NAS 同步异常 [{acc_name}]: {e}", exc_info=True)
                failed_accounts.append(acc_name)

        logger.info(f"NAS 同步完成，共 {total_synced} 条")
        return Response({
            'status': 'success',
            'count': total_synced,
            'failed_accounts': failed_accounts or None,
        })


class ProjectAliyunNASViewSet(viewsets.ModelViewSet):
    queryset = ProjectAliyunNAS.objects.all()
    serializer_class = ProjectAliyunNASSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'file_system_name': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
    }
    search_fields = ['file_system_name', 'project', 'owner', 'description']
    ordering_fields = ['file_system_name', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'file_system_name']


# -------------------- 阿里云 SLB --------------------
class AliyunSLBViewSet(viewsets.ReadOnlyModelViewSet, SyncActionMixin):
    queryset = AliyunSLB.objects.all()
    serializer_class = AliyunSLBSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region_id', 'address_type', 'network_type', 'status', 'pay_type', 'account_name']
    search_fields = ['load_balancer_id', 'load_balancer_name', 'address']
    ordering = ['-updated_at']

    # 关键：重写 retrieve，让详情接口也返回 { code: 200, data: ... }
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'msg': 'success',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def sync(self, request):
        logger.info('=== 开始同步阿里云 SLB（负载均衡） ===')
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置阿里云账号'}, status=400)

        total_synced = 0
        failed_accounts = []

        # 加载 SLB 项目映射（根据负载均衡器名称）
        slb_project_map = {}
        try:
            for record in ProjectAliyunSLB.objects.only('load_balancer_name', 'project', 'environment', 'owner', 'description').iterator():
                key = record.load_balancer_name.strip().lower()
                slb_project_map[key] = {
                    'project': record.project,
                    'environment': record.environment,
                    'owner': record.owner,
                    'remark': record.description,
                }
            logger.debug(f"加载 {len(slb_project_map)} 条SLB项目映射")
        except Exception as e:
            logger.error(f"SLB项目映射加载失败: {e}")


        for acc in accounts:
            acc_name = acc['name']
            try:
                for region in acc['regions']:
                    cfg = make_tea_config(acc, region, 'slb')
                    client = SlbClient(cfg)
                    runtime = RuntimeOptions()
                    runtime.autoretry = True
                    runtime.max_attempts = 3

                    page = 1
                    while True:
                        req = DescribeLoadBalancersRequest()
                        req.page_size = 100
                        req.page_number = page
                        # v2 SDK 必须显式传 region_id
                        req.region_id = region

                        resp = safe_api_call(
                            lambda: client.describe_load_balancers_with_options(req, runtime)
                        )

                        if not resp or not resp.body or not resp.body.load_balancers:
                            break

                        lbs = resp.body.load_balancers.load_balancer or []
                        if not lbs:
                            break

                        for lb in lbs:
                            # 获取监听端口（安全调用）
                            listener_ports = self._get_listener_ports(client, lb.load_balancer_id, runtime)

                            # 获取后端服务器（安全调用）
                            backend_servers = self._get_backend_servers(client, lb.load_balancer_id, runtime)

                            # 标签处理
                            tags = {}
                            if hasattr(lb, 'tags') and lb.tags and hasattr(lb.tags, 'tag'):
                                tags = {t.tag_key: t.tag_value for t in lb.tags.tag}

                            defaults = {
                                'load_balancer_name': getattr(lb, 'load_balancer_name', ''),
                                'region_id': region,
                                'address': getattr(lb, 'address', ''),
                                'address_type': getattr(lb, 'address_type', ''),
                                'network_type': getattr(lb, 'network_type', ''),
                                'vpc_id': getattr(lb, 'vpc_id', ''),
                                'vswitch_id': getattr(lb, 'v_switch_id', ''),
                                'load_balancer_spec': getattr(lb, 'load_balancer_spec', ''),
                                'status': getattr(lb, 'load_balancer_status', ''),
                                'creation_time': convert_utc_to_shanghai(getattr(lb, 'create_time', None)),
                                'account_name': acc_name,
                                'bandwidth': getattr(lb, 'bandwidth', 0) or 0,
                                'internet_charge_type': getattr(lb, 'internet_charge_type', ''),
                                'master_zone_id': getattr(lb, 'master_zone_id', ''),
                                'slave_zone_id': getattr(lb, 'slave_zone_id', ''),
                                'resource_group_id': getattr(lb, 'resource_group_id', ''),
                                'pay_type': getattr(lb, 'pay_type', ''),
                                'delete_protection': getattr(lb, 'delete_protection', 'off'),
                                'listener_ports': listener_ports,
                                'backend_servers': backend_servers,
                                'tags': tags,
                                'updated_at': django_timezone.now(),
                            }

                            # 应用项目映射（根据负载均衡器名称匹配）
                            lb_name_lower = defaults['load_balancer_name'].strip().lower()
                            project_info = slb_project_map.get(lb_name_lower, {})
                            if project_info:
                                defaults['project'] = project_info.get('project')
                                defaults['environment'] = project_info.get('environment')
                                defaults['owner'] = project_info.get('owner')
                                defaults['remark'] = project_info.get('remark')

                            try:
                                AliyunSLB.objects.update_or_create(
                                    load_balancer_id=lb.load_balancer_id,
                                    defaults=defaults
                                )
                                total_synced += 1
                            except Exception as db_err:
                                logger.error(f"保存 SLB {lb.load_balancer_id} 失败: {db_err}")

                        if len(lbs) < 100:
                            break
                        page += 1

            except Exception as e:
                logger.error(f"账号 [{acc_name}] SLB 同步异常: {e}", exc_info=True)
                failed_accounts.append(acc_name)

        log_msg = f"SLB 同步完成，共 {total_synced} 条"
        if failed_accounts:
            log_msg += f"，跳过无权限账号: {', '.join(failed_accounts)}"
        logger.info(log_msg)

        return Response({
            'status': 'success',
            'count': total_synced,
            'failed_accounts': failed_accounts or None,
            'synced_at': django_timezone.now(),
        })

    def _get_listener_ports(self, client, lb_id, runtime):
        req = DescribeLoadBalancerListenersRequest(load_balancer_id=lb_id)
        resp = safe_api_call(lambda: client.describe_load_balancer_listeners_with_options(req, runtime))
        if resp and resp.body and resp.body.listeners:
            return [l.listener_port for l in resp.body.listeners]
        return []

    def _get_backend_servers(self, client, lb_id, runtime):
        req = DescribeVServerGroupsRequest(load_balancer_id=lb_id)
        resp = safe_api_call(lambda: client.describe_vserver_groups_with_options(req, runtime))
        servers = []
        if resp and resp.body and resp.body.vserver_groups:
            for g in (resp.body.vserver_groups.vserver_group or []):
                g_req = DescribeVServerGroupAttributeRequest(vserver_group_id=g.vserver_group_id)
                g_resp = safe_api_call(lambda: client.describe_vserver_group_attribute_with_options(g_req, runtime))
                if g_resp and g_resp.body and g_resp.body.backend_servers:
                    for s in g_resp.body.backend_servers.backend_server or []:
                        servers.append({
                            'server_id': getattr(s, 'server_id', ''),
                            'weight': getattr(s, 'weight', 100)
                        })
        return servers


class ProjectAliyunSLBViewSet(viewsets.ModelViewSet):
    queryset = ProjectAliyunSLB.objects.all()
    serializer_class = ProjectAliyunSLBSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'load_balancer_name': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
    }
    search_fields = ['load_balancer_name', 'project', 'owner', 'description']
    ordering_fields = ['load_balancer_name', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'load_balancer_name']


class ProjectAliyunSLSViewSet(viewsets.ModelViewSet):
    queryset = ProjectAliyunSLS.objects.all()
    serializer_class = ProjectAliyunSLSSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'project_name': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
    }
    search_fields = ['project_name', 'project', 'owner', 'description']
    ordering_fields = ['project_name', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'project_name']


# -------------------- 阿里云 SLS --------------------
class AliyunSLSViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AliyunSLSProject.objects.prefetch_related('logstores').all()
    serializer_class = AliyunSLSProjectSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['region_id', 'status', 'account_name', 'data_redundancy_type', 'recycle_bin_enabled']
    search_fields = ['project_name', 'description']
    ordering = ['-updated_at']

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        同步阿里云SLS（日志服务）项目与Logstore
        """
        logger.info('=== 开始同步阿里云 SLS（日志服务） ===')
        accounts = get_aliyun_accounts()
        if not accounts:
            return Response({'status': 'error', 'message': '未配置阿里云账号'}, status=400)

        total_projects = 0
        total_logstores = 0
        failed_accounts = []

        # 加载 SLS 项目映射（根据Project名称）
        sls_project_map = {}
        try:
            for record in ProjectAliyunSLS.objects.only('project_name', 'project', 'environment', 'owner', 'description').iterator():
                key = record.project_name.strip() # Project名称大小写敏感，或者API里不敏感? 通常Project Name是全局唯一的。
                sls_project_map[key] = {
                    'project': record.project,
                    'environment': record.environment,
                    'owner': record.owner,
                    'remark': record.description,
                }
            logger.debug(f"加载 {len(sls_project_map)} 条SLS项目映射")
        except Exception as e:
            logger.error(f"SLS项目映射加载失败: {e}")

        for acc in accounts:
            acc_name = acc.get('name')
            if not acc_name:
                logger.warning(f"跳过没有名称的账号配置: {acc}")
                continue

            try:
                regions = acc.get('regions', [])
                if not regions:
                    logger.info(f"账号 [{acc_name}] 未配置区域，跳过")
                    continue

                for region in regions:
                    logger.info(f"同步账号 [{acc_name}] 区域 [{region}] 的SLS资源")
                    cfg = make_tea_config(acc, region, 'sls')
                    client = Sls20201230Client(cfg)
                    runtime = util_models.RuntimeOptions()
                    runtime.autoretry = True
                    runtime.max_attempts = 3
                    headers = {}

                    # 2. 分页获取所有Project
                    page = 1
                    page_size = 100
                    while True:
                        req = sls_models.ListProjectRequest()
                        req.offset = (page - 1) * page_size
                        req.size = page_size
                        resp = safe_api_call(
                            lambda: client.list_project_with_options(req, headers, runtime)
                        )
                        if not resp or not resp.body:
                            logger.warning(f"账号 [{acc_name}] 区域 [{region}] 第{page}页无响应")
                            break
                        project_list = getattr(resp.body, 'projects', []) or []
                        if not project_list:
                            logger.info(f"账号 [{acc_name}] 区域 [{region}] 第{page}页无项目")
                            break
                        logger.info(f"账号 [{acc_name}] 区域 [{region}] 第{page}页获取到 {len(project_list)} 个项目")

                        for p in project_list:
                            project_name = getattr(p, 'project_name', '')
                            if not project_name:
                                logger.warning("跳过没有名称的Project")
                                continue

                            # ===== 1. 处理 Project 详情 =====
                            data_redundancy_type = None
                            recycle_bin_enabled = None
                            # 注意：从日志看，项目详情字段在 resp.body 中，但代码调用的是 get_project_with_options
                            # 假设当前逻辑正确，根据日志调整字段提取
                            try:
                                # 调用 GetProject API 获取详情
                                project_detail_resp = safe_api_call(
                                    lambda: client.get_project_with_options(project_name, headers, runtime)
                                )
                                if project_detail_resp and project_detail_resp.body:
                                    project_detail = project_detail_resp.body
                                    # 使用 to_map() 确保获取到字典，然后安全取值
                                    detail_map = project_detail.to_map() if hasattr(project_detail, 'to_map') else {}
                                    data_redundancy_type = detail_map.get('dataRedundancyType')
                                    recycle_bin_enabled = detail_map.get('recycleBinEnabled')
                            except Exception as detail_e:
                                logger.warning(f"获取项目 [{project_name}] 详情异常，使用List数据: {detail_e}")
                                # 如果获取详情失败，尝试从列表响应 p 中获取（但列表可能不包含这些字段）
                                pass

                            # 准备项目数据 (直接从列表响应对象 p 获取基础字段)
                            defaults = {
                                'account_name': acc_name,
                                'region_id': region,
                                'description': getattr(p, 'description', None),
                                'status': getattr(p, 'status', None),
                                'create_time': convert_utc_to_shanghai(getattr(p, 'create_time', None)),
                                'last_modify_time': convert_utc_to_shanghai(getattr(p, 'last_modify_time', None)),
                                'updated_at': timezone.now(),
                                'data_redundancy_type': data_redundancy_type,  # 来自详情API或None
                                'recycle_bin_enabled': recycle_bin_enabled,  # 来自详情API或None
                            }

                            # 应用项目映射
                            # 注意：Project Name 是否大小写敏感？阿里云SLS Project名称是全局唯一的，且不支持大写字母。
                            # 这里使用 strict matching or lower matching.
                            # defaults['project_name'] 是API返回的。
                            p_name_key = project_name.strip()
                            project_info = sls_project_map.get(p_name_key, {})
                            if project_info:
                                defaults['project'] = project_info.get('project')
                                defaults['environment'] = project_info.get('environment')
                                defaults['owner'] = project_info.get('owner')
                                defaults['remark'] = project_info.get('remark')

                            try:
                                project, created = AliyunSLSProject.objects.update_or_create(
                                    project_name=project_name,
                                    defaults=defaults
                                )
                                total_projects += 1
                                if created:
                                    logger.info(f"创建新项目: {project_name}")
                                else:
                                    logger.debug(f"更新项目: {project_name}")

                                # ===== 2. 处理该项目的 Logstore 列表和详情 =====
                                try:
                                    list_req = sls_models.ListLogStoresRequest()
                                    list_req.offset = 0
                                    list_req.size = 500
                                    list_resp = safe_api_call(
                                        lambda: client.list_log_stores_with_options(
                                            project_name,
                                            list_req,
                                            headers,
                                            runtime
                                        )
                                    )
                                    if list_resp and list_resp.body:
                                        logstore_names = getattr(list_resp.body, 'logstores', []) or []
                                        logger.info(f"项目 [{project_name}] 发现 {len(logstore_names)} 个Logstore")

                                        for store_name in logstore_names:
                                            if not store_name:
                                                continue
                                            # 获取单个Logstore详情
                                            detail_resp = safe_api_call(
                                                lambda: client.get_log_store_with_options(
                                                    project_name,
                                                    store_name,
                                                    headers,
                                                    runtime
                                                )
                                            )
                                            if detail_resp and detail_resp.body:
                                                logstore_body = detail_resp.body
                                                # 将响应体转为字典以便统一处理
                                                logstore_map = logstore_body.to_map() if hasattr(logstore_body,
                                                                                                 'to_map') else {}



                                                # 构建Logstore数据字典 (严格对应模型字段名)
                                                # 注意：模型字段是蛇形命名，API返回是驼峰或混合，需正确映射
                                                store_defaults = {
                                                    # 基础信息
                                                    'account_name': acc_name,  # 显式设置账号名
                                                    'ttl': logstore_map.get('ttl'),
                                                    'shard_count': logstore_map.get('shardCount'),  # 注意映射
                                                    'enable_tracking': logstore_map.get('enable_tracking'),
                                                    'logstore_name': store_name,  # 确保名称被设置
                                                    # 配置信息
                                                    'auto_split': logstore_map.get('autoSplit'),
                                                    'max_split_shard': logstore_map.get('maxSplitShard'),
                                                    'append_meta': logstore_map.get('appendMeta'),
                                                    'telemetry_type': logstore_map.get('telemetryType'),
                                                    'mode': logstore_map.get('mode'),
                                                    'product_type': logstore_map.get('productType'),
                                                    # 存储信息
                                                    'hot_ttl': logstore_map.get('hot_ttl'),
                                                    'infrequent_access_ttl': logstore_map.get('infrequentAccessTTL'),
                                                    # 其他信息
                                                    'encrypt_conf': logstore_map.get('encrypt_conf'),
                                                    'processor_id': logstore_map.get('processorId'),
                                                    'sharding_policy': logstore_map.get('shardingPolicy'),
                                                    # 时间信息 (使用转换后的datetime对象)
                                                    'create_time': convert_utc_to_shanghai(
                                                        getattr(logstore_body, 'create_time', None)),
                                                    'last_modify_time': convert_utc_to_shanghai(
                                                        getattr(logstore_body, 'last_modify_time', None)),
                                                    'updated_at': timezone.now(),
                                                }
                                                # 移除值为None的项，避免覆盖数据库中的现有值（如果需要）
                                                # store_defaults = {k: v for k, v in store_defaults.items() if v is not None}
                                                try:
                                                    # 更新或创建Logstore记录
                                                    AliyunSLSLogStore.objects.update_or_create(
                                                        project=project,
                                                        logstore_name=store_name,
                                                        defaults=store_defaults
                                                    )
                                                    total_logstores += 1
                                                    logger.debug(f"成功同步Logstore: {store_name}")
                                                except Exception as save_e:
                                                    logger.error(f"保存Logstore [{store_name}] 到数据库失败: {save_e}")
                                            else:
                                                logger.warning(f"获取Logstore [{store_name}] 详情失败或返回为空")
                                    else:
                                        logger.warning(f"获取项目 [{project_name}] 的Logstore列表失败")
                                except Exception as logstore_e:
                                    logger.error(f"处理项目 [{project_name}] 的Logstore时发生异常: {logstore_e}")
                            except Exception as project_e:
                                logger.error(f"处理项目 [{project_name}] 失败: {project_e}")

                        # 判断是否还有下一页
                        if len(project_list) < page_size:
                            break
                        page += 1

            except Exception as e:
                logger.error(f"账号 [{acc_name}] SLS 同步异常: {e}", exc_info=True)
                failed_accounts.append(acc_name)

        # 生成同步结果日志
        log_msg = f"SLS 同步完成：{total_projects} 个 Project，{total_logstores} 个 Logstore"
        if failed_accounts:
            log_msg += f"，失败账号: {', '.join(failed_accounts)}"
        logger.info(log_msg)

        # 返回同步结果
        return Response({
            'status': 'success' if not failed_accounts else 'partial',
            'projects': total_projects,
            'logstores': total_logstores,
            'failed_accounts': failed_accounts or None,
            'synced_at': timezone.now(),
            'message': log_msg
        })


# -------------------- 阿里云 安全组 --------------------
# -------------------- 修改后的阿里云安全组 ViewSet --------------------
class AliyunSecurityGroupViewSet(viewsets.ModelViewSet):
    queryset = AliyunSecurityGroup.objects.all()
    serializer_class = AliyunSecurityGroupSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'security_group_id': ['exact', 'icontains'],
        'security_group_name': ['exact', 'icontains'],
        'vpc_id': ['exact'],
        'region_id': ['exact'],
        'account_name': ['exact', 'icontains'],
    }
    search_fields = ['security_group_id', 'security_group_name', 'description', 'vpc_id', 'account_name']
    ordering_fields = ['security_group_name', 'created_at', 'updated_at', 'creation_time']
    ordering = ['-updated_at']

    def _create_client(self, account: dict, region: str) -> EcsClient:
        """创建ECS客户端"""
        try:
            config = make_tea_config(account, region, 'ecs')
            config.connect_timeout = 5000
            config.read_timeout = 10000
            return EcsClient(config)
        except Exception as e:
            logger.error(f"创建ECS客户端失败 [{account['name']}/{region}]: {e}")
            return None

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """同步安全组数据（使用公共组件）"""
        # 添加明确的开始日志
        logger.info("=" * 50)
        logger.info("开始安全组同步任务")
        logger.info("=" * 50)

        accounts = get_aliyun_accounts()
        if not accounts:
            logger.warning("未配置阿里云账号，同步任务终止")
            return Response({'status': 'error', 'message': '未配置阿里云账号'}, status=400)

        total_groups = 0
        total_rules = 0
        failed_regions = []
        account_stats = []

        logger.info(f"共需处理 {len(accounts)} 个账号，预计同步 {sum(len(acc['regions']) for acc in accounts)} 个地域")

        for account in accounts:
            acc_name = account['name']
            acc_groups = 0
            acc_rules = 0

            logger.info(f"正在处理账号: {acc_name}（共 {len(account['regions'])} 个地域）")

            for region in account['regions']:
                client = self._create_client(account, region)
                if not client:
                    failed_regions.append(f"{acc_name}/{region}")
                    logger.error(f"账号 {acc_name} 地域 {region} 客户端创建失败")
                    continue

                runtime = util_models.RuntimeOptions()
                runtime.autoretry = True
                runtime.max_attempts = 3

                page = 1
                region_groups = 0
                region_rules = 0

                while True:
                    # 第一步：获取安全组列表
                    req = ecs_models.DescribeSecurityGroupsRequest(
                        region_id=region,
                        page_size=100,
                        page_number=page
                    )
                    req.is_query_ecs_count = True
                    req.is_query_rule_count = True

                    def call_security_groups():
                        return client.describe_security_groups_with_options(req, runtime)

                    resp = safe_api_call(call_security_groups)
                    if not resp or not resp.body:
                        logger.warning(f"[{acc_name}/{region}] 第 {page} 页获取安全组列表失败")
                        break

                    groups = resp.body.security_groups.security_group if resp.body.security_groups else []
                    if not groups:
                        logger.info(f"[{acc_name}/{region}] 第 {page} 页未获取到安全组数据")
                        break

                    # 获取安全组列表后 - 输出获取了多少组
                    logger.info(f"[{acc_name}/{region}] 第 {page} 页成功获取 {len(groups)} 个安全组")
                    region_groups += len(groups)

                    for sg in groups:
                        try:
                            # 处理标签
                            tags = {}
                            if hasattr(sg, 'tags') and sg.tags:
                                tag_list = getattr(sg.tags, 'tag', [])
                                if tag_list:
                                    for tag in tag_list:
                                        if hasattr(tag, 'tag_key') and hasattr(tag, 'tag_value'):
                                            tags[tag.tag_key] = tag.tag_value

                            # 准备安全组数据
                            defaults = {
                                'security_group_name': sg.security_group_name or '',
                                'vpc_id': getattr(sg, 'vpc_id', ''),
                                'region_id': region,
                                'account_name': acc_name,
                                'description': getattr(sg, 'description', ''),
                                'creation_time': convert_utc_to_shanghai(getattr(sg, 'creation_time', None)),
                                'value': getattr(sg, 'value', ''),
                                'ecs_count': getattr(sg, 'ecs_count', 0) or 0,
                                'rule_count': getattr(sg, 'rule_count', 0) or 0,
                                'tags': tags,
                                'updated_at': django_timezone.now(),
                            }

                            # 保存安全组
                            with transaction.atomic():
                                group, created = AliyunSecurityGroup.objects.update_or_create(
                                    security_group_id=sg.security_group_id,
                                    defaults=defaults
                                )

                            if created:
                                total_groups += 1
                                acc_groups += 1
                                logger.debug(f"新建安全组: {sg.security_group_id}")

                            # 第二步：获取安全组规则
                            rule_req = ecs_models.DescribeSecurityGroupAttributeRequest(
                                security_group_id=sg.security_group_id,
                                region_id=region,
                            )

                            def call_security_group_rules():
                                return client.describe_security_group_attribute_with_options(rule_req, runtime)

                            rule_resp = safe_api_call(call_security_group_rules)
                            if not rule_resp or not rule_resp.body:
                                logger.warning(f"[{acc_name}/{region}] 安全组 {sg.security_group_id} 规则获取失败")
                                continue

                            # 处理规则
                            permissions = rule_resp.body.permissions
                            if permissions:
                                rules = permissions.permission if hasattr(permissions, 'permission') else []

                                # 获取安全组规则后 - 输出获取了多少规则
                                if rules:
                                    logger.info(
                                        f"[{acc_name}/{region}][{sg.security_group_id}] 获取到 {len(rules)} 条规则")
                                    region_rules += len(rules)

                                for rule in rules:
                                    raw_create_time = getattr(rule, 'create_time', None)
                                    ipv6_source = getattr(rule, 'ipv_6source_cidr_ip', None) or getattr(rule,
                                                                                                        'ipv6_source_cidr_ip',
                                                                                                        None)
                                    ipv6_dest = getattr(rule, 'ipv_6dest_cidr_ip', None) or getattr(rule,
                                                                                                    'ipv6_dest_cidr_ip',
                                                                                                    None)

                                    rule_defaults = {
                                        'security_group': group,
                                        'direction': rule.direction,
                                        'ip_protocol': getattr(rule, 'ip_protocol', 'all').lower(),
                                        'port_range': getattr(rule, 'port_range', '-1/-1'),
                                        'source_cidr_ip': getattr(rule, 'source_cidr_ip', ''),
                                        'dest_cidr_ip': getattr(rule, 'dest_cidr_ip', ''),
                                        'policy': getattr(rule, 'policy', 'accept').lower(),
                                        'priority': int(getattr(rule, 'priority', 1)),
                                        'description': getattr(rule, 'description', ''),
                                        'creation_time': raw_create_time or '',
                                        'source_group_id': getattr(rule, 'source_group_id', ''),
                                        'source_group_owner_account': getattr(rule, 'source_group_owner_account', ''),
                                        'dest_group_id': getattr(rule, 'dest_group_id', ''),
                                        'dest_group_owner_account': getattr(rule, 'dest_group_owner_account', ''),
                                        'ipv6_source_cidr_ip': ipv6_source or '',
                                        'ipv6_dest_cidr_ip': ipv6_dest or '',
                                        'source_prefix_list_id': getattr(rule, 'source_prefix_list_id', ''),
                                        'dest_prefix_list_id': getattr(rule, 'dest_prefix_list_id', ''),
                                        'updated_at': django_timezone.now(),
                                    }

                                    with transaction.atomic():
                                        AliyunSecurityGroupRule.objects.update_or_create(
                                            rule_id=rule.security_group_rule_id,
                                            defaults=rule_defaults
                                        )
                                    total_rules += 1
                                    acc_rules += 1

                        except Exception as e:
                            logger.error(f"处理安全组 {getattr(sg, 'security_group_id', 'N/A')} 失败: {e}",
                                         exc_info=True)
                            continue

                    if len(groups) < 100:
                        logger.info(f"[{acc_name}/{region}] 已达到最后一页，停止分页")
                        break
                    page += 1
                    time.sleep(0.1)

                logger.info(f"[{acc_name}/{region}] 同步完成，本区域共 {region_groups} 个安全组，{region_rules} 条规则")

            account_stats.append({
                'account': acc_name,
                'groups': acc_groups,
                'rules': acc_rules
            })

        # 同步完成后 - 输出同步完成日志
        logger.info("=" * 50)
        logger.info(f"安全组同步任务完成")
        logger.info(f"总计: {total_groups} 个安全组，{total_rules} 条规则")
        logger.info(f"成功账号: {len([stat for stat in account_stats if stat['groups'] > 0])} 个")
        if failed_regions:
            logger.warning(f"失败地域数: {len(failed_regions)} 个")
        logger.info("=" * 50)

        return Response({
            'status': 'success',
            'total_groups': total_groups,
            'total_rules': total_rules,
            'accounts': account_stats,
            'failed_regions': failed_regions or None,
            'synced_at': django_timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    def retrieve(self, request, *args, **kwargs):
        """获取安全组详情（重写以使用统一响应格式）"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return ApiResponse.success(data=serializer.data)
        except Exception as e:
            logger.error(f"获取安全组详情失败: {e}")
            return ApiResponse.error(msg=f"获取详情失败: {str(e)}")

    @action(detail=True, methods=['get'])
    def instances(self, request, pk=None):
        """获取安全组关联的ECS实例（使用分页）"""
        sg = self.get_object()

        from aliyun.models import AliyunECS
        from aliyun.serializers import AliyunECSSerializer

        try:
            logger.info(f"查询安全组 {sg.security_group_id} 关联的ECS实例")

            # 查询关联的ECS实例
            ecs_instances = AliyunECS.objects.filter(
                security_group_ids__contains=[sg.security_group_id]
            ).order_by('-creation_time')

            serializer = AliyunECSSerializer(ecs_instances, many=True)
            return ApiResponse.success(data={
                'page': 1,
                'total': len(serializer.data),
                'pageSize': len(serializer.data),
                'data': serializer.data
            })

        except Exception as e:
            logger.error(f"获取关联实例失败: {e}", exc_info=True)
            return ApiResponse.error(msg=f"获取关联实例失败: {str(e)}")


class AliyunSecurityGroupRuleViewSet(viewsets.ModelViewSet):
    queryset = AliyunSecurityGroupRule.objects.all()
    serializer_class = AliyunSecurityGroupRuleSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'security_group__security_group_id': ['exact'],
        'direction': ['exact'],
        'ip_protocol': ['exact'],
        'policy': ['exact'],
    }
    search_fields = ['port_range', 'source_cidr_ip', 'dest_cidr_ip', 'description']
    ordering_fields = ['priority', 'creation_time']
    ordering = ['security_group', 'direction', 'priority']

    def get_queryset(self):
        queryset = super().get_queryset()
        security_group_id = self.request.query_params.get('security_group_id')
        if security_group_id:
            queryset = queryset.filter(security_group__security_group_id=security_group_id)
        return queryset