import csv
import json
import os
import re
import ssl
from datetime import datetime, timezone
from pathlib import Path
import time

import dotenv
from django_filters.rest_framework import DjangoFilterBackend
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from rest_framework import generics, filters, viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from dateutil import parser as iso_parser
import logging
import pytz
from rest_framework import viewsets, status


from .filters import *
from .models import *

from .serializers import *
from apps.utils.pagination import CustomPagination
from datetime import datetime, timezone
logger = logging.getLogger(__name__)


def load_vcenter_config():
    """从配置文件加载 vCenter 连接信息"""
    config_path = Path(__file__).parent / 'conf' / 'vcenter.cnf'
    vcenters = []
    current_vc = {}
    vc_num = None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 解析 VC1_HOST, VC2_USER 等格式
                    if key.startswith('VC') and '_' in key:
                        num = key.split('_')[0][2:]  # 提取数字
                        field = key.split('_', 1)[1].lower()  # host, user, password
                        
                        if vc_num != num:
                            if current_vc and all(k in current_vc for k in ['host', 'user', 'password']):
                                vcenters.append(current_vc)
                            current_vc = {}
                            vc_num = num
                        
                        current_vc[field] = value
            
            # 添加最后一个
            if current_vc and all(k in current_vc for k in ['host', 'user', 'password']):
                vcenters.append(current_vc)
                
        logger.info(f"成功加载 {len(vcenters)} 个 vCenter 配置")
    except Exception as e:
        logger.error(f"加载 vCenter 配置失败: {str(e)}")
    
    return vcenters


class VMwareVMViewSet(viewsets.ModelViewSet):
    """VMware 虚拟机资产 ViewSet"""
    queryset = VMwareVM.objects.all()
    serializer_class = VMwareVMSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VMwareVMFilter
    pagination_class = CustomPagination
    search_fields = ['name', 'owner', 'project_name', 'ip_address']
    ordering_fields = ['last_sync', 'name', 'status']
    ordering = ['-last_sync']

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """同步 vCenter 虚拟机数据到数据库"""
        vcenters = load_vcenter_config()
        
        if not vcenters:
            return Response({
                'code': 400,
                'msg': 'vCenter 配置为空，请检查 datacenter/conf/vcenter.cnf 文件'
            }, status=status.HTTP_400_BAD_REQUEST)

        total_synced = 0
        sync_results = []

        for vc in vcenters:
            connector = VCenterConnector(vc['host'], vc['user'], vc['password'])
            if connector.connect():
                try:
                    vms = connector.get_vms()
                    for vm_data in vms:
                        disks = vm_data.pop('data_disks', [])
                        for disk in disks:
                            disk['disk_type'] = str(disk['disk_type'])

                        VMwareVM.objects.update_or_create(
                            vm_uuid=vm_data['vm_uuid'],
                            defaults={
                                **vm_data,
                                'data_disks': disks,
                                'last_sync': datetime.now()
                            }
                        )
                    total_synced += len(vms)
                    sync_results.append({
                        'vcenter': vc['host'],
                        'status': 'success',
                        'count': len(vms)
                    })
                    logger.info(f"已同步 {len(vms)} 台虚拟机来自 {vc['host']}")
                except Exception as e:
                    sync_results.append({
                        'vcenter': vc['host'],
                        'status': 'error',
                        'message': str(e)
                    })
                    logger.error(f"同步失败[{vc['host']}]: {str(e)}")
                finally:
                    connector.disconnect()
            else:
                sync_results.append({
                    'vcenter': vc['host'],
                    'status': 'connection_failed'
                })

        return Response({
            'code': 200,
            'msg': f'同步完成，共计 {total_synced} 台虚拟机',
            'data': {
                'total': total_synced,
                'details': sync_results
            }
        })


class VMwareVMDashboard(generics.ListAPIView):
    queryset = VMwareVM.objects.all()
    serializer_class = VMwareVMSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = VMwareVMFilter

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            stats = {
                'total': queryset.count(),
                'powered_on': queryset.filter(status='poweredOn').count(),
                'powered_off': queryset.filter(status='poweredOff').count(),
                'env_counts': dict(
                    queryset.values_list('environment_type')
                    .annotate(count=Count('environment_type'))
                    .order_by('-count')
                )
            }
            last_sync = queryset.order_by('-last_sync').first()
            response_data = {
                'stats': stats,
                'last_sync_time': last_sync.last_sync if last_sync else None,
                'vm_list': self.get_serializer(queryset, many=True).data
            }
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error handling VMwareVMDashboard request: {str(e)}")
            raise APIException(f"An error occurred: {str(e)}")


class VCenterConnector:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.service_instance = None
        self.project_data = self._load_project_data()

    def _load_project_data(self):
        """从数据库加载项目信息"""
        project_map = {}
        try:
            # 从 ProjectVMware 表加载项目信息
            records = ProjectVMware.objects.all()
            for record in records:
                hostname_key = record.hostname.strip().lower()
                project_map[hostname_key] = {
                    'project': record.project,
                    'environment': record.environment,
                    'owner': record.owner,
                }
            logger.info(f"成功从数据库加载 {len(project_map)} 条项目数据")
        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}")
        return project_map

    def _enrich_vm_data(self, vm_info):
        lookup_key = vm_info['name'].strip().lower()
        project_info = self.project_data.get(
            lookup_key,
            {'project': '未分配', 'environment': '未分类', 'owner': '系统管理员'}
        )
        if 'nb_last_backup' in vm_info:
            try:
                parts = vm_info['nb_last_backup'].split(',')
                if len(parts) >= 3:
                    time_str = parts[0].strip()
                    backup_time = datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y %z')
                    vm_info['last_backup'] = backup_time
                    vm_info['backup_policy'] = parts[2].strip()
            except Exception as e:
                logger.warning(f"解析 NetBackup 信息失败: {str(e)}")
        return {**vm_info, 'project_info': project_info}

    def get_disk_type(self, device):
        """精确获取磁盘类型"""
        backing = device.backing
        try:
            if isinstance(backing, vim.vm.device.VirtualDisk.FlatVer2BackingInfo):
                return 'thin' if backing.thinProvisioned else 'thick'
            elif isinstance(backing, vim.vm.device.VirtualDisk.SparseVer2BackingInfo):
                return 'sparse'
            elif isinstance(backing, vim.vm.device.VirtualDisk.RawDiskVer2BackingInfo):
                return 'raw'
            elif isinstance(backing, vim.vm.device.VirtualDisk.SeSparseBackingInfo):
                return 'sesparse'
            else:
                return 'unknown'
        except AttributeError:
            return 'unknown'

    def connect(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        try:
            self.service_instance = SmartConnect(
                host=self.host, user=self.user, pwd=self.password,
                port=443, sslContext=context)
            return True
        except Exception as e:
            logger.error(f"连接失败[{self.host}]: {str(e)}")
            return False

    def get_vms(self):
        """获取所有虚拟机数据（含磁盘信息）"""
        if not self.service_instance:
            return []
        try:
            content = self.service_instance.RetrieveContent()
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.VirtualMachine], True)
            vms = []
            for vm in container.view:
                try:
                    lookup_key = vm.name.strip().lower()
                    project_info = self.project_data.get(
                        lookup_key,
                        {'project': '未分配', 'environment': '未分类', 'owner': '系统管理员'}
                    )

                    # 获取 NetBackup 信息
                    backup_time = None
                    backup_policy = ''
                    custom_fields = vm.availableField
                    nb_field = None
                    for field in custom_fields:
                        if field.name == 'NB_LAST_BACKUP':
                            nb_field = field
                            break
                    if nb_field:
                        for value in vm.value:
                            if value.key == nb_field.key:
                                try:
                                    parts = value.value.split(',')
                                    if len(parts) >= 3:
                                        time_str = parts[0].strip()
                                        backup_time = datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y %z')
                                        backup_policy = parts[2].strip()
                                except Exception as e:
                                    logger.warning(f"解析 NetBackup 信息失败: {str(e)}")
                                break

                    # 获取磁盘信息
                    disks = []
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualDisk):
                            provisioned_gb = round(device.capacityInBytes / (1024 ** 3), 2)
                            used_bytes = 0
                            try:
                                if hasattr(vm.storage, 'perDatastoreUsage'):
                                    for usage in vm.storage.perDatastoreUsage:
                                        if device.backing.datastore == usage.datastore:
                                            used_bytes = usage.committed
                                            break
                            except Exception as e:
                                logger.warning(f"磁盘空间计算异常 {vm.name}: {str(e)}")
                            used_gb = round(used_bytes / (1024 ** 3), 2) if used_bytes > 0 else 0.0
                            if used_gb > provisioned_gb * 1.1:
                                used_gb = provisioned_gb
                            disks.append({
                                'disk_id': str(device.key),
                                'provisioned_gb': provisioned_gb,
                                'used_gb': used_gb,
                                'disk_type': self.get_disk_type(device),
                                'datastore': device.backing.datastore.name if device.backing.datastore else ''
                            })

                    # 获取创建日期
                    creation_date = getattr(vm.config, 'createDate', None)
                    if creation_date:
                        creation_date = creation_date.replace(microsecond=0)

                    # 获取主IP地址
                    # 获取主IP地址 - 按优先级匹配指定网段
                    ip_address = None

                    # 定义优先级网段（按顺序匹配）
                    priority_prefixes = ['10.164.', '9.25.', '10.227.']

                    if hasattr(vm.guest, 'net') and vm.guest.net:
                        # 先尝试匹配优先级网段
                        for prefix in priority_prefixes:
                            for net in vm.guest.net:
                                if hasattr(net, 'ipAddress') and net.ipAddress:
                                    for ip in net.ipAddress:
                                        # 跳过IPv6地址
                                        if ':' in ip:
                                            continue
                                        if ip.startswith(prefix):
                                            ip_address = ip
                                            break  # 跳出 IP 循环
                                if ip_address:
                                    break  # 跳出网卡循环
                            if ip_address:
                                break  # 跳出前缀循环

                        # 如果没匹配到优先级网段，回退到任意 10.x 网段
                        if not ip_address:
                            for net in vm.guest.net:
                                if hasattr(net, 'ipAddress') and net.ipAddress:
                                    for ip in net.ipAddress:
                                        if ':' in ip:
                                            continue
                                        if ip.startswith('10.'):
                                            ip_address = ip
                                            break
                                if ip_address:
                                    break

                        # 最后回退：取第一个IPv4地址
                        if not ip_address:
                            for net in vm.guest.net:
                                if hasattr(net, 'ipAddress') and net.ipAddress:
                                    for ip in net.ipAddress:
                                        if ':' not in ip:  # 第一个IPv4
                                            ip_address = ip
                                            break
                                if ip_address:
                                    break

                    vm_info = {
                        'vm_uuid': vm.summary.config.uuid,
                        'name': vm.name,
                        'status': vm.runtime.powerState,
                        'ip_address': ip_address,
                        'os_name': getattr(vm.guest, 'guestFullName', '') or '',
                        'cpu_cores': vm.config.hardware.numCPU,
                        'cpu_usage': vm.summary.quickStats.overallCpuUsage or 0,
                        'memory_mb': vm.summary.config.memorySizeMB,
                        'vcenter_host': self.host,
                        'uptime_seconds': getattr(vm.summary.quickStats, 'uptimeSeconds', 0) or 0,
                        'tools_version': getattr(vm.guest, 'toolsVersion', '') or '',
                        'tools_status': getattr(vm.guest, 'toolsStatus', 'guestToolsNotInstalled'),
                        'tools_running_status': getattr(vm.guest, 'toolsRunningStatus', 'guestToolsNotRunning'),
                        'last_boot': vm.runtime.bootTime,
                        'last_backup': backup_time,
                        'backup_policy': backup_policy,
                        'annotation': vm.summary.config.annotation or '',
                        'environment_type': project_info['environment'],
                        'project_name': project_info['project'],
                        'owner': project_info['owner'],
                        'data_disks': disks,
                        'creation_date': creation_date,
                    }
                    vms.append(vm_info)
                except Exception as e:
                    logger.warning(f"VM数据处理错误 {vm.name}: {str(e)}")
            return vms
        except Exception as e:
            logger.error(f"API错误[{self.host}]: {str(e)}")
            return []

    def disconnect(self):
        if self.service_instance:
            try:
                Disconnect(self.service_instance)
            except Exception as e:
                logger.error(f"断开连接错误[{self.host}]: {str(e)}")


class ProjectBareMetalViewSet(viewsets.ModelViewSet):
    queryset = ProjectBareMetal.objects.all()
    serializer_class = ProjectBareMetalSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'hostname': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
        'ip_address': ['exact', 'icontains'],
        'vendor': ['exact', 'icontains'],
        'data_center': ['exact', 'icontains'],
        'device_type': ['exact'],
        'os_name': ['exact', 'icontains'],
        'virtualization_type': ['exact'],
    }
    search_fields = [
        'hostname', 'project', 'owner', 'ip_address', 'os_name',
        'model', 'serial_number', 'asset_code', 'vendor', 'data_center',
        'management_ip', 'description',
    ]
    ordering_fields = [
        'hostname', 'project', 'environment', 'owner', 'vendor',
        'data_center', 'production_date', 'warranty_expire', 'created_at',
    ]
    ordering = ['project', 'hostname']


class ProjectNetworkDeviceViewSet(viewsets.ModelViewSet):
    queryset = ProjectNetworkDevice.objects.all()
    serializer_class = ProjectNetworkDeviceSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'hostname': ['exact', 'icontains'],
        'management_ip': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
        'device_type': ['exact'],
        'vendor': ['exact'],
        'status': ['exact'],
        'connection_method': ['exact'],
    }
    search_fields = [
        'hostname', 'project', 'owner', 'management_ip',
        'os_info', 'model', 'serial_number', 'software_version', 'location'
    ]
    ordering_fields = [
        'hostname', 'project', 'environment', 'owner',
        'device_type', 'purchase_date', 'warranty_expire', 'created_at'
    ]
    ordering = ['project', 'hostname']


class ProjectVMwareViewSet(viewsets.ModelViewSet):
    queryset = ProjectVMware.objects.all()
    serializer_class = ProjectVMwareSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'hostname': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
    }
    search_fields = ['hostname', 'project', 'owner']
    ordering_fields = ['hostname', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'hostname']


class ProjectProxmoxViewSet(viewsets.ModelViewSet):
    queryset = ProjectProxmox.objects.all()
    serializer_class = ProjectProxmoxSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'hostname': ['exact', 'icontains'],
        'vmid': ['exact', 'icontains'],
        'project': ['exact', 'icontains'],
        'environment': ['exact'],
        'owner': ['exact', 'icontains'],
    }
    search_fields = ['hostname', 'vmid', 'project', 'owner', 'description']
    ordering_fields = ['hostname', 'vmid', 'project', 'environment', 'owner', 'created_at']
    ordering = ['project', 'hostname']


def load_proxmox_config():
    """从配置文件加载 Proxmox VE 连接信息"""
    config_path = Path(__file__).parent / 'conf' / 'proxmox.cnf'
    clusters = []
    current_pve = {}
    pve_num = None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 解析 PVE1_HOST, PVE2_USER 等格式
                    if key.startswith('PVE') and '_' in key:
                        num = key.split('_')[0][3:]  # 提取数字
                        field = key.split('_', 1)[1].lower()  # host, user, token, password, verify_ssl
                        
                        if pve_num != num:
                            if current_pve and 'host' in current_pve and 'user' in current_pve:
                                clusters.append(current_pve)
                            current_pve = {}
                            pve_num = num
                        
                        if field == 'verify_ssl':
                            current_pve[field] = value.lower() in ('true', '1', 'yes')
                        else:
                            current_pve[field] = value
            
            # 添加最后一个
            if current_pve and 'host' in current_pve and 'user' in current_pve:
                clusters.append(current_pve)
                
        logger.info(f"成功加载 {len(clusters)} 个 Proxmox VE 配置")
    except Exception as e:
        logger.error(f"加载 Proxmox VE 配置失败: {str(e)}")
    
    return clusters


class ProxmoxConnector:
    """Proxmox VE API 连接器"""
    
    def __init__(self, host, user, token=None, password=None, verify_ssl=False):
        self.host = host
        self.base_url = f"https://{host}:8006/api2/json"
        self.verify_ssl = verify_ssl
        self.headers = {}
        self.cluster_name = host  # 默认使用host作为集群名
        self.project_data = self._load_project_data()
        
        if token:
            # API Token 认证（推荐）
            self.headers['Authorization'] = f'PVEAPIToken={token}'
        elif password:
            # 密码认证
            self._auth_with_password(user, password)
        else:
            logger.error(f"Proxmox [{host}]: 未提供 Token 或密码")
    
    def _auth_with_password(self, user, password):
        """密码认证获取 ticket"""
        try:
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            resp = requests.post(
                f"{self.base_url}/access/ticket",
                data={'username': user, 'password': password},
                verify=self.verify_ssl,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()['data']
            self.headers = {
                'Cookie': f"PVEAuthCookie={data['ticket']}",
                'CSRFPreventionToken': data['CSRFPreventionToken']
            }
            logger.info(f"Proxmox [{self.host}]: 密码认证成功")
        except Exception as e:
            logger.error(f"Proxmox [{self.host}]: 密码认证失败 - {str(e)}")
    
    def _load_project_data(self):
        """从数据库加载项目信息（基于VMID匹配）"""
        project_map = {}
        try:
            records = ProjectProxmox.objects.all()
            for record in records:
                vmid_key = str(record.vmid).strip()
                project_map[vmid_key] = {
                    'project': record.project,
                    'environment': record.environment,
                    'owner': record.owner,
                    'description': record.description or '',
                }
            logger.info(f"成功从数据库加载 {len(project_map)} 条 Proxmox 项目数据")
        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}")
        return project_map
    
    def _api_get(self, endpoint):
        """发起 API GET 请求"""
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        try:
            resp = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=60
            )
            resp.raise_for_status()
            return resp.json().get('data', [])
        except Exception as e:
            logger.error(f"Proxmox API 请求失败 [{endpoint}]: {str(e)}")
            return []
    
    def get_nodes(self):
        """获取集群所有节点"""
        return self._api_get('/nodes')
    
    def get_cluster_status(self):
        """获取集群状态信息"""
        status_data = self._api_get('/cluster/status')
        for item in status_data:
            if item.get('type') == 'cluster':
                self.cluster_name = item.get('name', self.host)
                break
        return status_data
    
    def get_vms(self, node):
        """获取节点上的虚拟机列表"""
        return self._api_get(f'/nodes/{node}/qemu')
    
    def get_vm_config(self, node, vmid):
        """获取虚拟机详细配置"""
        return self._api_get(f'/nodes/{node}/qemu/{vmid}/config')
    
    def get_vm_status(self, node, vmid):
        """获取虚拟机运行状态"""
        return self._api_get(f'/nodes/{node}/qemu/{vmid}/status/current')

    def get_vm_agent_info(self, node, vmid):
        """获取 Guest Agent 信息（静默处理权限错误）"""
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        try:  # ← 确保这里有 try:
            endpoint = f'/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces'
            resp = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            if resp.status_code == 403:
                return None
            if resp.status_code == 500:
                return None
            resp.raise_for_status()

            response_data = resp.json()
            agent_data = response_data.get('data', {})

            if isinstance(agent_data, dict):
                return agent_data.get('result', [])
            elif isinstance(agent_data, list):
                return agent_data
            else:
                return []

        except Exception as e:  # ← 对应这里的 except
            logger.debug(f"VM {vmid} agent info error: {str(e)}")
            return []


    def get_ha_resources(self):
        """获取高可用资源列表"""
        return self._api_get('/cluster/ha/resources')

    def get_vm_backups(self, node, vmid):
        """获取 VM 的备份信息（修正版本）"""
        backups = []

        # 1. 获取当前节点的存储列表
        node_storages = self._api_get(f'/nodes/{node}/storage')
        if not node_storages:
            logger.warning(f"节点 {node} 没有可用的存储")
            return []

        # 2. 支持的备份存储类型（添加 'pbs' 和 'pbs-vm'）
        SUPPORTED_BACKUP_TYPES = {'pbs', 'dir', 'nfs', 'btrfs', 'zfspool', 'lvm', 'lvmthin'}

        for storage_info in node_storages:
            storage = storage_info.get('storage')
            storage_type = storage_info.get('type', '')

            # 跳过不可用的存储
            if storage_info.get('disable') or not storage:
                continue

            # 检查存储类型是否支持备份（注意：pbs 类型是 Proxmox Backup Server）
            # 实际上，几乎所有存储类型都可以存储备份，除了某些特殊类型
            # 更安全的方式是：不根据类型过滤，而是尝试查询，失败则跳过

            try:
                # 使用节点级 API 查询备份内容
                contents = self._api_get(
                    f'/nodes/{node}/storage/{storage}/content?content=backup'
                )

                # 如果返回 None 或空列表，说明没有备份或查询失败
                if not contents:
                    logger.debug(f"存储 {storage} (类型: {storage_type}) 没有备份数据")
                    continue

                # 遍历备份内容，筛选当前 VM
                found_in_storage = 0
                for item in contents:
                    if str(item.get('vmid', '')) == str(vmid):
                        backups.append({
                            'volid': item.get('volid'),
                            'size': item.get('size', 0),
                            'ctime': item.get('ctime'),
                            'format': item.get('format', ''),
                            'storage': storage,
                            'subtype': item.get('subtype', ''),
                            'notes': item.get('notes', ''),
                            'verification': item.get('verification', {}).get('state', ''),
                        })
                        found_in_storage += 1

                if found_in_storage > 0:
                    logger.info(f"VM {vmid} 在存储 {storage} 中找到 {found_in_storage} 个备份")

            except Exception as e:
                error_msg = str(e)
                # 静默处理存储不可用的情况
                if any(x in error_msg.lower() for x in ['not available', 'does not exist', 'not implemented']):
                    logger.debug(f"存储 {storage} 在节点 {node} 上不可用或类型不支持: {error_msg[:80]}")
                else:
                    logger.warning(f"查询存储 {storage} 失败: {error_msg[:100]}")
                continue

        # 按时间倒序排序
        backups.sort(key=lambda x: x.get('ctime', 0), reverse=True)

        if backups:
            logger.info(f"VM {vmid} 共找到 {len(backups)} 个备份")
        else:
            logger.debug(f"VM {vmid} 未找到任何备份")

        return backups

    def get_all_vms(self):
        """获取所有节点上的虚拟机信息"""
        all_vms = []
        
        # 获取集群名称
        self.get_cluster_status()
        
        # 获取HA资源映射
        ha_resources = {}
        for ha in self.get_ha_resources():
            # sid 格式: vm:100
            sid = ha.get('sid', '')
            if sid.startswith('vm:'):
                vmid = sid.split(':')[1]
                ha_resources[vmid] = {
                    'state': ha.get('state', ''),
                    'group': ha.get('group', '')
                }
        
        # 遍历所有节点
        nodes = self.get_nodes()
        for node_info in nodes:
            node = node_info.get('node')
            if not node:
                continue
            
            # 获取节点上的虚拟机
            vms = self.get_vms(node)
            for vm in vms:
                try:
                    vmid = str(vm.get('vmid'))
                    
                    # 获取详细配置
                    config = self.get_vm_config(node, vmid)
                    status_info = self.get_vm_status(node, vmid)
                    
                    # 解析磁盘信息
                    disks = []
                    boot_disk_gb = 0
                    total_disk_gb = 0
                    storage = ''
                    
                    for key, value in config.items():
                        if key.startswith(('scsi', 'virtio', 'ide', 'sata')) and isinstance(value, str):
                            # 解析磁盘配置，格式如: local-lvm:vm-100-disk-0,size=32G
                            if ':' in value:
                                parts = value.split(',')
                                disk_storage = parts[0].split(':')[0] if ':' in parts[0] else ''
                                size_gb = 0
                                for part in parts:
                                    if part.startswith('size='):
                                        size_str = part.split('=')[1]
                                        if size_str.endswith('G'):
                                            size_gb = float(size_str[:-1])
                                        elif size_str.endswith('T'):
                                            size_gb = float(size_str[:-1]) * 1024
                                        elif size_str.endswith('M'):
                                            size_gb = float(size_str[:-1]) / 1024
                                
                                disks.append({
                                    'device': key,
                                    'storage': disk_storage,
                                    'size_gb': size_gb
                                })
                                total_disk_gb += size_gb
                                
                                # 第一个磁盘作为引导磁盘
                                if not storage:
                                    storage = disk_storage
                                    boot_disk_gb = size_gb

                    # 获取IP地址（从agent或配置）
                    ip_address = ''
                    mac_address = ''
                    agent_running = False
                    ALLOWED_NETWORK_PREFIXES = ('10.164.', '10.227.')

                    def parse_agent_enabled(config):
                        """
                        精准解析 Proxmox VE agent 配置是否启用
                        API 参考: https://pve.proxmox.com/pve-docs/api-viewer/index.html#/nodes/{node}/qemu/{vmid}/config

                        agent 字段格式:
                        - "1"                    -> 启用
                        - "1,fstrim_cloned_disks=1"  -> 启用（逗号分隔的选项）
                        - "enabled=1,type=virtio"    -> 启用（键值对格式）
                        - "0" 或 ""              -> 禁用
                        """
                        agent_value = config.get('agent')

                        # 空值检查
                        if not agent_value:
                            return False

                        agent_str = str(agent_value).strip()

                        # 空字符串
                        if not agent_str:
                            return False

                        # 明确禁用
                        if agent_str in ('0', 'disabled'):
                            return False

                        # 启用判断：以"1"开头 或 包含"enabled=1"
                        # 覆盖 "1", "1,xxx", "enabled=1", "enabled=1,xxx" 等格式
                        if agent_str.startswith('1') or 'enabled=1' in agent_str:
                            return True

                        return False

                    # 直接尝试调用 agent 接口，不依赖配置
                    agent_net = self.get_vm_agent_info(node, vmid)

                    if agent_net:
                        agent_running = True
                        logger.info(f"VM {vmid} agent returned {len(agent_net)} interfaces")

                        for iface in agent_net:
                            if not isinstance(iface, dict):
                                continue

                            iface_name = iface.get('name', '')
                            if iface_name in ('lo', 'Loopback Pseudo-Interface 1') or \
                                    iface_name.startswith(('kube-ipvs', 'flannel', 'cni', 'veth', 'docker', 'br-',
                                                           'isatap', 'Teredo')):
                                continue

                            ip_addrs = iface.get('ip-addresses', [])
                            for addr in ip_addrs:
                                if not isinstance(addr, dict):
                                    continue
                                ip_type = addr.get('ip-address-type', '')
                                ip_val = addr.get('ip-address', '')
                                if ip_type == 'ipv4' and ip_val and ip_val.startswith(ALLOWED_NETWORK_PREFIXES):
                                    ip_address = ip_val
                                    logger.info(f"VM {vmid} IP found: {ip_address} (interface: {iface_name})")
                                    break
                            if ip_address:
                                break
                    else:
                        logger.debug(f"VM {vmid} agent returned no data")

                    # 记录配置状态（用于前端展示）
                    agent_enabled = parse_agent_enabled(config)
                    
                    # 解析网络配置获取MAC地址
                    for key, value in config.items():
                        if key.startswith('net') and isinstance(value, str):
                            parts = value.split(',')
                            for part in parts:
                                if '=' in part:
                                    k, v = part.split('=', 1)
                                    if k in ('virtio', 'e1000', 'rtl8139', 'vmxnet3'):
                                        mac_address = v
                                        break
                            if mac_address:
                                break
                    
                    # 匹配项目信息
                    project_info = self.project_data.get(
                        vmid,
                        {'project': '未分配', 'environment': '未分类', 'owner': '系统管理员', 'description': ''}
                    )
                    
                    # HA信息
                    ha_info = ha_resources.get(vmid, {'state': '', 'group': ''})

                    # 获取备份信息
                    backups = self.get_vm_backups(node, vmid)

                    # 准备备份相关数据
                    last_backup = None
                    last_backup_volid = ''
                    last_backup_size = 0
                    last_backup_format = ''
                    last_backup_status = ''
                    backup_storage = ''
                    backup_history = []

                    if backups:
                        # 最新备份
                        latest = backups[0]
                        last_backup_ts = latest.get('ctime')
                        if last_backup_ts:
                            last_backup = datetime.fromtimestamp(last_backup_ts, tz=timezone.utc)
                        last_backup_volid = latest.get('volid', '')
                        last_backup_size = latest.get('size', 0)
                        last_backup_format = latest.get('format', '')
                        last_backup_status = latest.get('verification', '')
                        backup_storage = latest.get('storage', '')

                        # 历史记录（最近5个）
                        backup_history = [
                            {
                                'volid': b.get('volid'),
                                'ctime': b.get('ctime'),
                                'size': b.get('size'),
                                'format': b.get('format'),
                                'date': datetime.fromtimestamp(b.get('ctime', 0), tz=timezone.utc).isoformat()
                            }
                            for b in backups[:5]
                        ]
                    
                    vm_info = {
                        'vmid': vmid,
                        'node': node,
                        'cluster': self.cluster_name,
                        'pool': vm.get('pool', ''),
                        'name': vm.get('name', f'VM-{vmid}'),
                        'status': vm.get('status', 'stopped'),
                        'template': bool(vm.get('template', 0)),
                        'cpu_cores': config.get('cores', 1),
                        'cpu_sockets': config.get('sockets', 1),
                        'memory_mb': config.get('memory', 512),
                        'boot_disk_gb': boot_disk_gb,
                        'total_disk_gb': total_disk_gb,
                        'bios_type': 'ovmf' if config.get('bios') == 'ovmf' else 'seabios',
                        'ip_address': ip_address,
                        'mac_address': mac_address,
                        'os_type': config.get('ostype', ''),
                        'uptime': status_info.get('uptime', 0) if isinstance(status_info, dict) else 0,
                        'ha_state': ha_info['state'],
                        'ha_group': ha_info['group'],
                        'agent_enabled': agent_enabled,
                        'agent_running': agent_running,
                        'storage': storage,
                        'disk_info': disks,
                        'project_name': project_info['project'],
                        'environment_type': project_info['environment'],
                        'owner': project_info['owner'],
                        'description': project_info['description'],
                        'last_backup': last_backup,
                        'last_backup_volid': last_backup_volid,
                        'last_backup_size': last_backup_size,
                        'last_backup_format': last_backup_format,
                        'last_backup_status': last_backup_status,
                        'backup_storage': backup_storage,
                        'backup_count': len(backups),
                        'backup_history': backup_history,
                    }
                    all_vms.append(vm_info)
                    
                except Exception as e:
                    logger.warning(f"处理VM {vm.get('vmid')} 失败: {str(e)}")
        
        return all_vms



class ProxmoxVMViewSet(viewsets.ModelViewSet):
    """Proxmox 虚拟机资产 ViewSet"""
    queryset = ProxmoxVM.objects.all()
    serializer_class = ProxmoxVMSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProxmoxVMFilter
    pagination_class = CustomPagination
    search_fields = ['vmid', 'name', 'node', 'cluster', 'project_name', 'owner', 'ip_address', 'description']
    ordering_fields = ['last_sync', 'vmid', 'name', 'node', 'status', 'project_name']
    ordering = ['-last_sync']

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """同步 Proxmox VE 虚拟机数据到数据库"""
        from django.utils import timezone as dj_timezone
        
        clusters = load_proxmox_config()
        
        if not clusters:
            return Response({
                'code': 400,
                'msg': 'Proxmox VE 配置为空，请检查 datacenter/conf/proxmox.cnf 文件'
            }, status=status.HTTP_400_BAD_REQUEST)

        total_synced = 0
        sync_results = []

        for pve in clusters:
            connector = ProxmoxConnector(
                host=pve['host'],
                user=pve['user'],
                token=pve.get('token'),
                password=pve.get('password'),
                verify_ssl=pve.get('verify_ssl', False)
            )
            
            try:
                vms = connector.get_all_vms()
                for vm_data in vms:
                    ProxmoxVM.objects.update_or_create(
                        vmid=vm_data['vmid'],
                        defaults={
                            **vm_data,
                            'last_sync': dj_timezone.now()
                        }
                    )
                total_synced += len(vms)
                sync_results.append({
                    'cluster': pve['host'],
                    'status': 'success',
                    'count': len(vms)
                })
                logger.info(f"已同步 {len(vms)} 台虚拟机来自 {pve['host']}")
            except Exception as e:
                sync_results.append({
                    'cluster': pve['host'],
                    'status': 'error',
                    'message': str(e)
                })
                logger.error(f"同步失败[{pve['host']}]: {str(e)}")

        return Response({
            'code': 200,
            'msg': f'同步完成，共计 {total_synced} 台虚拟机',
            'data': {
                'total': total_synced,
                'details': sync_results
            }
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取统计数据"""
        queryset = self.filter_queryset(self.get_queryset())

        # 手动处理 backup_status（因为 filter_backup_status 是自定义 method，
        # 在 stats 中不会被自动应用，除非重新实例化 FilterSet）
        backup_status = request.query_params.get('backup_status')
        if backup_status == 'backed_up':
            queryset = queryset.filter(last_backup__isnull=False)
        elif backup_status == 'no_backup':
            queryset = queryset.filter(last_backup__isnull=True)

        # 或者更优雅的方式：使用同一个 FilterSet 处理
        # filterset = self.filterset_class(request.query_params, queryset=self.get_queryset())
        # queryset = filterset.qs

        total = queryset.count()
        running = queryset.filter(status='running').count()
        stopped = queryset.filter(status='stopped').count()
        ha_enabled = queryset.exclude(ha_state='').exclude(ha_state__isnull=True).count()
        no_backup = queryset.filter(last_backup__isnull=True).count()
        backed_up = queryset.filter(last_backup__isnull=False).count()  # 添加已备份统计

        # 环境分布
        from django.db.models import Count
        env_counts = dict(
            queryset.values_list('environment_type')
            .annotate(count=Count('environment_type'))
            .order_by('-count')
        )

        # 节点分布
        node_counts = dict(
            queryset.values_list('node')
            .annotate(count=Count('node'))
            .order_by('-count')
        )

        # 最后同步时间
        last_sync = queryset.order_by('-last_sync').first()

        return Response({
            'total': total,
            'running': running,
            'stopped': stopped,
            'ha_enabled': ha_enabled,
            'no_backup': no_backup,
            'backed_up': backed_up,  # 返回已备份数量
            'env_counts': env_counts,
            'node_counts': node_counts,
            'last_sync_time': last_sync.last_sync if last_sync else None
        })