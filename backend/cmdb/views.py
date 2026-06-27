import logging
import ipaddress
from django.shortcuts import render
from collections import defaultdict  # 添加这一行
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework import generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import NetworkSegment, IPAddress, cmdbdatabase
from .serializers import NetworkSegmentSerializer, IPAddressSerializer, cmdbdatabaseSerializer
from apps.utils.response import ApiResponse

# Import models for Sync
from datacenter.models import VMwareVM, ProjectNetworkDevice, ProjectBareMetal, ProxmoxVM
from aliyun.models import AliyunECS, AliyunSLB, AliyunEIP

from apps.utils.pagination import CustomPagination

logger = logging.getLogger(__name__)

class NetworkSegmentViewSet(viewsets.ModelViewSet):
    queryset = NetworkSegment.objects.all()
    serializer_class = NetworkSegmentSerializer
    search_fields = ['name', 'segment', 'description']
    filterset_fields = ['type', 'vlan_id']


class IPAddressViewSet(viewsets.ModelViewSet):
    queryset = IPAddress.objects.all().order_by('ip_address')
    serializer_class = IPAddressSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ip_address', 'hostname', 'owner', 'description', 'bound_instance_name']
    filterset_fields = ['type', 'status', 'source', 'environment', 'network_segment']
    ordering_fields = ['ip_address', 'updated_at']

    def get_queryset(self):
        queryset = super().get_queryset()

        type_param = self.request.query_params.get('type')
        segment_param = self.request.query_params.get('segment')
        logger.info(f"IP查询请求 - type: {type_param}, segment: {segment_param}, 用户: {self.request.user}")

        # 支持按网段筛选
        if segment_param:
            try:
                # 验证网段格式并计算范围
                network = ipaddress.ip_network(segment_param + '/24', strict=False)
                # 获取网段内所有可能的IP列表
                network_ips = [str(ip) for ip in network.hosts()]
                # 使用 Django 的 __in 查询
                queryset = queryset.filter(ip_address__in=network_ips)
                logger.info(f"网段筛选: {segment_param}, 匹配IP数: {queryset.count()}")
            except ValueError as e:
                logger.warning(f"无效的网段参数: {segment_param}, 错误: {e}")

        return queryset

    @action(detail=False, methods=['get'], url_path='segments')
    def segments(self, request):
        """
        获取网段统计信息（用于前端网段卡片展示）
        支持参数: type=internet/intranet
        """
        try:
            ip_type = request.query_params.get('type', 'internet')

            # 获取该类型的所有IP
            queryset = IPAddress.objects.filter(type=ip_type)

            logger.info(f"网段统计请求 - type: {ip_type}, 总IP数: {queryset.count()}")

            # 按网段分组统计
            segment_stats = defaultdict(lambda: {
                'network': '',
                'cidr': '',
                'total': 254,
                'used': 0,
                'available': 0,
                'reserved': 0,
                'deprecated': 0,
                'usage': 0.0
            })

            for ip_obj in queryset:
                try:
                    ip = ipaddress.ip_address(ip_obj.ip_address)
                    # 计算 /24 网段地址
                    # 将 IP 地址转换为网络地址 (如 192.168.1.5 -> 192.168.1.0)
                    ip_str = str(ip)
                    parts = ip_str.split('.')
                    if len(parts) == 4:
                        network_addr = f"{parts[0]}.{parts[1]}.{parts[2]}.0"

                        if not segment_stats[network_addr]['network']:
                            segment_stats[network_addr]['network'] = network_addr
                            segment_stats[network_addr]['cidr'] = f"{network_addr}/24"

                        # 统计各状态
                        status_key = ip_obj.status
                        if status_key in ['used', 'available', 'reserved', 'deprecated']:
                            segment_stats[network_addr][status_key] += 1

                except ValueError as e:
                    logger.warning(f"无效IP地址: {ip_obj.ip_address}, 错误: {e}")
                    continue

            # 计算使用率并格式化结果
            result = []
            for network_addr, stats in segment_stats.items():
                if not network_addr:
                    continue

                # 已分配 = 使用中 + 保留 + 废弃
                allocated = stats['used'] + stats['reserved'] + stats['deprecated']
                # 使用率
                stats['usage'] = round((allocated / stats['total']) * 100, 1)
                # 空闲数
                stats['available'] = stats['total'] - allocated

                result.append(stats)

            # 按网段地址排序
            def ip_key(x):
                try:
                    return [int(i) for i in x['network'].split('.')]
                except:
                    return [0, 0, 0, 0]

            result.sort(key=ip_key)

            logger.info(f"网段统计完成 - 共 {len(result)} 个网段")
            return ApiResponse.success(data=result)

        except Exception as e:
            logger.error(f"网段统计接口错误: {str(e)}", exc_info=True)
            return ApiResponse.error(msg=f"获取网段统计失败: {str(e)}")

    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request):
        """同步各端IP地址信息"""
        try:
            stats = {
                'total': 0,
                'created': 0,
                'updated': 0,
                'errors': 0
            }
            
            with transaction.atomic():
                # 1. Sync Aliyun ECS
                self._sync_aliyun_ecs(stats)
                
                # 2. Sync Aliyun SLB
                self._sync_aliyun_slb(stats)
                
                # 3. Sync Aliyun EIP
                self._sync_aliyun_eip(stats)
                
                # 4. Sync VMware VMs
                self._sync_vmware_vm(stats)
                
                # 5. Sync Project Network Devices
                self._sync_network_devices(stats)
                
                # 6. Sync Project Bare Metal
                self._sync_bare_metal(stats)
                
                # 7. Sync Proxmox VMs
                self._sync_proxmox_vm(stats)

            return ApiResponse.success(data=stats, msg=f"同步完成：新增 {stats['created']}，更新 {stats['updated']}，错误 {stats['errors']}")
        except Exception as e:
            logger.error(f"IP Sync failed: {str(e)}")
            return ApiResponse.error(msg=f"同步失败: {str(e)}")

    def _update_or_create_ip(self, ip_addr, data, stats, resource_instance=None):
        """Helper to create or update IP record"""
        try:
            if not ip_addr or ip_addr in ['-', '']:
                return

            # Clean IP (remove whitespace)
            ip_addr = ip_addr.strip()
            
            # Simple check if valid IP
            try:
                ip_obj = ipaddress.ip_address(ip_addr)
            except ValueError:
                return

            # Determine Intranet vs Internet
            # Strictly use IANA private IP definition
            # is_private returns True for 10.x, 172.16-31.x, 192.168.x
            data['type'] = 'intranet' if ip_obj.is_private else 'internet'

            # Bind resource if provided
            if resource_instance:
                data['content_type'] = ContentType.objects.get_for_model(resource_instance)
                data['object_id'] = resource_instance.pk

            # Update or Create
            obj, created = IPAddress.objects.update_or_create(
                ip_address=ip_addr,
                defaults=data
            )
            
            if created:
                stats['created'] += 1
            else:
                stats['updated'] += 1
            stats['total'] += 1
            
        except Exception as e:
            logger.error(f"Error processing IP {ip_addr}: {str(e)}")
            stats['errors'] += 1

    def _sync_aliyun_ecs(self, stats):
        """Sync Aliyun ECS IPs"""
        # ECS has public_ip (single), eip (single), and system/data disks... wait, networks
        # Model fields: public_ip, private_ip, eip, ipv6
        queryset = AliyunECS.objects.all()
        for ecs in queryset:
            base_data = {
                'source': 'aliyun',
                'hostname': ecs.hostname or ecs.instance_name,
                'status': 'used',
                'environment': ecs.environment,
                'owner': ecs.owner,
                'bound_instance_name': ecs.instance_name
            }
            
            # Private IP
            if ecs.private_ip:
                data = base_data.copy()
                data['type'] = 'intranet'
                data['description'] = f"阿里云ECS: {ecs.instance_name} (私网)"
                self._update_or_create_ip(ecs.private_ip, data, stats, ecs)
                
            # Public IP
            if ecs.public_ip:
                data = base_data.copy()
                data['type'] = 'internet'
                data['description'] = f"阿里云ECS: {ecs.instance_name} (公网)"
                self._update_or_create_ip(ecs.public_ip, data, stats, ecs)

            # EIP
            if ecs.eip:
                data = base_data.copy()
                data['type'] = 'internet'
                data['description'] = f"阿里云ECS: {ecs.instance_name} (EIP)"
                self._update_or_create_ip(ecs.eip, data, stats, ecs)

    def _sync_aliyun_slb(self, stats):
        """Sync Aliyun SLB IPs"""
        queryset = AliyunSLB.objects.all()
        for slb in queryset:
            base_data = {
                'source': 'aliyun',
                'hostname': slb.load_balancer_name,
                'status': 'used' if slb.status == 'active' else 'available',
                'environment': 'prod', # Default or map if available
                'bound_instance_name': slb.load_balancer_name,
                'description': f"阿里云SLB: {slb.load_balancer_name}"
            }
            
            data = base_data.copy()
            data['type'] = 'internet' if slb.address_type == 'internet' else 'intranet'
            self._update_or_create_ip(slb.address, data, stats, slb)

    def _sync_aliyun_eip(self, stats):
        """Sync Aliyun EIPs"""
        queryset = AliyunEIP.objects.all()
        for eip in queryset:
            base_data = {
                'source': 'aliyun',
                'hostname': eip.name,
                'status': 'used' if eip.status == 'InUse' else 'available',
                'bound_instance_name': eip.name,
                'type': 'internet',
                'description': f"阿里云EIP: {eip.name}"
            }
            self._update_or_create_ip(eip.ip_address, base_data, stats, eip)

    def _sync_vmware_vm(self, stats):
        """Sync VMware VM IPs"""
        queryset = VMwareVM.objects.all()
        for vm in queryset:
            if not vm.ip_address:
                continue
                
            base_data = {
                'source': 'datacenter',
                'hostname': vm.name,
                'status': 'used' if vm.status == 'poweredOn' else 'available',
                'environment': vm.environment_type,
                'owner': vm.owner,
                'bound_instance_name': vm.name,
                'type': 'intranet', # Mostly intranet
                'description': f"VMware虚拟机: {vm.name} ({vm.annotation or ''})"
            }
            self._update_or_create_ip(vm.ip_address, base_data, stats, vm)

    def _sync_network_devices(self, stats):
        """Sync Network Devices Management IPs"""
        queryset = ProjectNetworkDevice.objects.all()
        for dev in queryset:
            if not dev.management_ip:
                continue

            base_data = {
                'source': 'datacenter',
                'hostname': dev.hostname,
                'status': 'used',
                'environment': dev.environment,
                'owner': dev.owner,
                'bound_instance_name': dev.hostname,
                'type': 'intranet',
                'location': dev.location,
                'description': f"网络设备: {dev.device_type} {dev.model}"
            }
            self._update_or_create_ip(dev.management_ip, base_data, stats, dev)

    def _sync_bare_metal(self, stats):
        """Sync Bare Metal IPs (业务IP、虚拟化IP、管理IP)"""
        queryset = ProjectBareMetal.objects.all()
        for server in queryset:
            base_data = {
                'source': 'datacenter',
                'hostname': server.hostname,
                'status': 'used',
                'environment': server.environment,
                'owner': server.owner,
                'bound_instance_name': server.hostname,
                'type': 'intranet',
            }

            # 1. 业务IP
            if server.ip_address:
                data = base_data.copy()
                data['description'] = f"物理机业务IP: {server.model or ''} S/N:{server.serial_number or ''}"
                self._update_or_create_ip(server.ip_address, data, stats, server)

            # 2. 虚拟化IP
            if server.virtualization_ip:
                data = base_data.copy()
                data['description'] = f"物理机虚拟化IP: {server.hostname} ({server.virtualization_type or ''})"
                self._update_or_create_ip(server.virtualization_ip, data, stats, server)

            # 3. 管理IP (iDRAC/IPMI)
            if server.management_ip:
                data = base_data.copy()
                data['description'] = f"物理机管理IP: {server.hostname} (带外管理)"
                self._update_or_create_ip(server.management_ip, data, stats, server)

    def _sync_proxmox_vm(self, stats):
        """Sync Proxmox VM IPs"""
        queryset = ProxmoxVM.objects.all()
        for vm in queryset:
            if not vm.ip_address:
                continue

            base_data = {
                'source': 'datacenter',
                'hostname': vm.name,
                'mac_address': vm.mac_address or '',
                'status': 'used' if vm.status == 'running' else 'available',
                'bound_instance_name': f"{vm.name} (VMID: {vm.vmid})",
                'type': 'intranet',
                'description': f"Proxmox虚拟机: {vm.name} @ {vm.node}"
            }
            self._update_or_create_ip(vm.ip_address, base_data, stats, vm)


class cmdbdatabaseViewSet(viewsets.ModelViewSet):
    queryset = cmdbdatabase.objects.all()
    serializer_class = cmdbdatabaseSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'name': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
        'host': ['exact', 'icontains'],
        'db_type': ['exact'],
    }
    search_fields = [
        'name', 'project', 'owner', 'host',
        'instance', 'db_name', 'version'
    ]
    ordering_fields = [
        'name', 'project', 'environment', 'owner',
        'created_at', 'updated_at'
    ]
    ordering = ['project', 'name']