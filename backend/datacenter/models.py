
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import JSONField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def validate_disk_structure(value):
    """验证系统盘结构"""
    required_keys = ['device', 'category', 'size']
    if not all(key in value for key in required_keys):
        raise ValidationError(f"系统盘结构不完整，必须包含 {required_keys} 字段")


class VMwareVM(models.Model):
    class StatusChoices(models.TextChoices):
        POWERED_ON = 'poweredOn', _('运行中')
        POWERED_OFF = 'poweredOff', _('已关闭')
        SUSPENDED = 'suspended', _('已挂起')

    class ToolsStatusChoices(models.TextChoices):
        NOT_INSTALLED = 'guestToolsNotInstalled', _('未安装')
        NEED_UPGRADE = 'guestToolsNeedUpgrade', _('需要升级')
        CURRENT = 'guestToolsCurrent', _('最新版本')
        UNMANAGED = 'guestToolsUnmanaged', _('未管理')
        SUPPORTED_NEW = 'guestToolsSupportedNew', _('新版支持')

    class ToolsRunningStatusChoices(models.TextChoices):
        NOT_RUNNING = 'guestToolsNotRunning', _('未运行')
        RUNNING = 'guestToolsRunning', _('运行中')
        EXECUTING_SCRIPTS = 'guestToolsExecutingScripts', _('执行脚本')

    # 唯一标识字段
    vm_uuid = models.CharField(
        _('虚拟机UUID'),
        max_length=128,
        unique=True,
        db_index=True
    )

    # 基础信息
    name = models.CharField(_('主机名'), max_length=255)
    vcenter_host = models.CharField(_('vCenter主机'), max_length=255)
    ip_address = models.GenericIPAddressField(
        _('IP地址'),
        null=True,
        blank=True
    )

    # 状态信息
    status = models.CharField(
        _('电源状态'),
        max_length=20,
        choices=StatusChoices.choices
    )
    tools_status = models.CharField(
        _('Tools版本状态'),
        max_length=50,
        choices=ToolsStatusChoices.choices,
        default=ToolsStatusChoices.NOT_INSTALLED
    )
    tools_running_status = models.CharField(
        _('Tools运行状态'),
        max_length=50,
        choices=ToolsRunningStatusChoices.choices,
        default=ToolsRunningStatusChoices.NOT_RUNNING
    )
    tools_version = models.CharField(
        _('Tools版本'),
        max_length=20,
        default='',
        blank=True
    )

    # 资源信息
    cpu_cores = models.PositiveSmallIntegerField(_('CPU核心数'))
    cpu_usage = models.PositiveSmallIntegerField(_('CPU使用率(%)'), default=0)
    memory_mb = models.PositiveIntegerField(_('内存(MB)'))

    # 系统信息
    os_name = models.CharField(
        _('操作系统'),
        max_length=255,
        blank=True,
        default=''
    )
    last_boot = models.DateTimeField(
        _('最后启动时间'),
        null=True,
        blank=True
    )
    uptime_seconds = models.BigIntegerField(
        _('运行时间(秒)'),
        default=0
    )

    data_disks = models.JSONField(
        '磁盘信息',
        default=list,
        validators=[validate_disk_structure],
        help_text="存储磁盘详细信息"
    )

    # 备份信息
    last_backup = models.DateTimeField(
        _('最后备份时间'),
        null=True,
        blank=True
    )
    backup_policy = models.CharField(
        _('备份策略'),
        max_length=100,
        blank=True,
        default=''
    )

    # 管理信息
    environment_type = models.CharField(
        _('环境类型'),
        max_length=50,
        default='未分类'
    )
    project_name = models.CharField(
        _('所属项目'),
        max_length=255,
        default='未分配'
    )
    owner = models.CharField(
        _('负责人'),
        max_length=50,
        default='系统管理员'
    )
    annotation = models.TextField(
        _('备注'),
        blank=True
    )
    creation_date = models.DateTimeField(
        _('创建日期'),
        null=True,
        blank=True,
        help_text="虚拟机创建/部署时间"
    )
    last_sync = models.DateTimeField(
        _('最后同步时间'),
        default=timezone.now
    )

    class Meta:
        verbose_name = _('虚拟机')
        verbose_name_plural = _('虚拟机')
        ordering = ['-last_sync']
        indexes = [
            models.Index(fields=['vcenter_host', 'status']),
            models.Index(fields=['environment_type']),
            models.Index(fields=['last_backup']),
        ]

    def __str__(self):
        return f"{self.name} ({self.vcenter_host})"

    @property
    def memory_gb(self):
        """内存GB显示值"""
        return round(self.memory_mb / 1024, 2)

    # 新增格式化方法
    @property
    def formatted_creation_date(self):
        if not self.creation_date:
            return "未知"
        return self.creation_date.strftime('%Y-%m-%d %H:%M:%S')  # 精确到秒

    @property
    def formatted_uptime(self):
        """格式化的运行时间"""
        if self.uptime_seconds <= 0:
            return _("未运行")

        days = self.uptime_seconds // 86400
        hours = (self.uptime_seconds % 86400) // 3600
        return f"{days}天{hours}小时"

    def get_status_display(self):
        return dict(self.StatusChoices.choices).get(
            self.status,
            _('未知状态')
        )

    def get_tools_status_display(self):
        return dict(self.ToolsStatusChoices.choices).get(
            self.tools_status,
            _('未知版本状态')
        )

    def get_tools_running_status_display(self):
        return dict(self.ToolsRunningStatusChoices.choices).get(
            self.tools_running_status,
            _('未知运行状态')
        )

    def parse_netbackup_info(self, nb_info):
        """解析 NetBackup 信息字符串

        格式示例: "Mon Oct 24 19:00:39 2022 +0800,hnbuvm,DEV-VM-butterflydev-1d-1m"
        """
        try:
            if not nb_info:
                return None, None

            parts = nb_info.split(',')
            if len(parts) >= 3:
                # 解析时间字符串
                time_str = parts[0].strip()
                backup_time = datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y %z')

                # 获取备份策略
                policy = parts[2].strip()

                return backup_time, policy
            return None, None
        except Exception as e:
            logger.error(f"解析 NetBackup 信息失败: {str(e)}")
            return None, None

    def update_from_vcenter(self, vm_object):
        """从 vCenter 对象更新虚拟机信息

        Args:
            vm_object: pyVmomi.vim.VirtualMachine 对象
        """
        try:
            # 获取 NetBackup 自定义属性
            custom_fields = vm_object.availableField
            nb_field = None

            # 查找 NetBackup 字段
            for field in custom_fields:
                if field.name == 'NB_LAST_BACKUP':
                    nb_field = field
                    break

            if nb_field:
                # 获取字段值
                for value in vm_object.value:
                    if value.key == nb_field.key:
                        backup_time, policy = self.parse_netbackup_info(value.value)
                        if backup_time:
                            self.last_backup = timezone.make_aware(backup_time)
                            self.backup_policy = policy
                            self.save(update_fields=['last_backup', 'backup_policy'])
                        break

            return True
        except Exception as e:
            logger.error(f"从 vCenter 更新备份信息失败: {str(e)}")
            return False

    @property
    def formatted_last_backup(self):
        """格式化最后备份时间"""
        if not self.last_backup:
            return _('未备份')
        return self.last_backup.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def backup_age_days(self):
        """计算备份年龄（天数）"""
        if not self.last_backup:
            return None
        return (timezone.now() - self.last_backup).days

    @property
    def is_backup_healthy(self):
        """检查备份是否健康"""
        if not self.last_backup:
            return False
        # 如果备份超过30天，认为不健康
        if self.backup_age_days and self.backup_age_days > 30:
            return False
        return True

    # 新增磁盘信息字段
    data_disks = models.JSONField(
        '磁盘信息',
        default=list,
        validators=[
            validate_disk_structure  # 需要新增验证器
        ],
        help_text="JSON格式存储磁盘信息，结构：["
                  "{'disk_id': '1000', 'provisioned_gb': 100, "
                  "'used_gb': 50, 'disk_type': 'thin', 'datastore': 'datastore1'}]"
    )

    # 新增验证方法（放在类外）
    def validate_disk_structure(value):
        """验证磁盘数据结构"""
        required_keys = ['disk_id', 'provisioned_gb', 'used_gb', 'disk_type']
        for item in value:
            if not all(key in item for key in required_keys):
                raise ValidationError(f"磁盘结构缺少必要字段，必须包含：{required_keys}")

    # 新增计算属性
    @property
    def total_provisioned(self):
        """总置备空间（自动计算）"""
        return sum(disk['provisioned_gb'] for disk in self.data_disks)

    @property
    def total_used(self):
        """总已用空间（自动计算）"""
        return sum(disk['used_gb'] for disk in self.data_disks)

    @property
    def overall_efficiency(self):
        """整体空间利用率"""
        if self.total_provisioned == 0:
            return 0.0
        return round((self.total_used / self.total_provisioned) * 100, 2)

    # 新增格式化方法
    def format_disk_info(self):
        """格式化磁盘信息显示"""
        try:
            if not self.data_disks:
                return "无磁盘信息"

            output = []
            for disk in self.data_disks:
                output.append(
                    f"磁盘{disk['disk_id']}: "
                    f"{self.get_disk_type_display(disk['disk_type'])} "
                    f"{disk['provisioned_gb']}GB置备 / "
                    f"{disk['used_gb']}GB已用 "
                    f"({disk['datastore']})"
                )
            return "<br>".join(output)
        except Exception as e:
            return f"磁盘信息解析错误: {str(e)}"

    # 新增类型显示映射
    def get_disk_type_display(self, disk_type):
        type_map = {
            'thin': '精简置备',
            'thick': '厚置备',
            'eagerZeroedThick': '即时清零厚置备'
        }
        return type_map.get(disk_type, '未知类型')


class ProjectBareMetal(models.Model):
    """物理机项目元数据管理"""

    # ========== 基础信息 ==========
    hostname = models.CharField(
        "主机名", max_length=255, unique=True,
        help_text="物理机唯一标识符"
    )
    ip_address = models.CharField(
        "业务IP", max_length=100,
        help_text="业务使用的IP地址/虚拟化地址"
    )
    project = models.CharField(
        "所属项目", max_length=255,
        help_text="物理机归属的项目名称"
    )
    environment = models.CharField(
        "环境类型", max_length=50,
        help_text="运行环境（如生产、测试、预发布）"
    )
    owner = models.CharField(
        "负责人", max_length=100, blank=True, null=True,
        help_text="物理机的主要负责人"
    )
    department = models.CharField(
        "部门", max_length=100, blank=True, null=True,
        help_text="负责人所属部门"
    )
    asset_code = models.CharField(
        "资产编号", max_length=255, unique=True, blank=True, null=True,
        help_text="企业资产唯一编号"
    )
    vendor = models.CharField(
        "厂商", max_length=255, blank=True, null=True,
        help_text="物理机品牌（如Dell、HP、浪潮）"
    )
    model = models.CharField(
        "型号", max_length=255, blank=True, null=True,
        help_text="物理机具体型号"
    )
    device_type = models.CharField(
        "设备类型", max_length=100, blank=True, null=True
    )
    serial_number = models.CharField(
        "序列号", max_length=255, unique=True, blank=True, null=True,
        help_text="厂商出厂序列号"
    )
    express_service_code = models.CharField(
        "快速服务代码", max_length=255, blank=True, null=True,
        help_text="厂商快速服务代码"
    )
    data_center = models.CharField(
        "数据中心", max_length=255, blank=True, null=True,
        help_text="物理机所在的数据中心"
    )
    u_count = models.CharField(
        "U数", max_length=50, blank=True, null=True,
        help_text="设备高度（如2U）"
    )
    rack_position = models.CharField(
        "机柜位置", max_length=255, blank=True, null=True,
        help_text="U位描述，如U01-U02"
    )
    cabinet = models.CharField(
        "所属机柜", max_length=255, blank=True, null=True,
        help_text="所在机柜编号"
    )
    room = models.CharField(
        "所属机房", max_length=255, blank=True, null=True,
        help_text="所在机房名称"
    )
    production_date = models.DateTimeField(
        "生产日期", blank=True, null=True,
        help_text="物理机的出厂生产日期"
    )
    warranty_expire = models.DateTimeField(
        "保修到期时间", blank=True, null=True,
        help_text="硬件保修到期日期"
    )
    rack_time = models.DateTimeField(
        "上架时间", blank=True, null=True,
        help_text="物理机上架投入使用的时间"
    )
    description = models.TextField(
        "说明", blank=True, null=True,
        help_text="附加备注信息"
    )

    # ========== 硬件信息 ==========
    cpu_model = models.CharField(
        "CPU型号", max_length=255, blank=True, null=True,
        help_text="如Intel Xeon Gold 6248"
    )
    cpu_count = models.CharField(
        "CPU数量", max_length=50, blank=True, null=True,
        help_text="物理CPU颗数"
    )
    cpu_cores = models.CharField(
        "CPU内核数", max_length=50, blank=True, null=True,
        help_text="每颗CPU的物理内核数"
    )
    cpu_logical_processors = models.CharField(
        "逻辑处理器", max_length=50, blank=True, null=True,
        help_text="逻辑处理器总数"
    )
    memory_size = models.CharField(
        "内存总容量", max_length=100, blank=True, null=True,
        help_text="如256GB"
    )
    memory_detail = models.CharField(
        "内存组合", max_length=255, blank=True, null=True,
        help_text="如16GB DDR4 * 16"
    )
    disk = models.CharField(
        "磁盘概要", max_length=500, blank=True, null=True,
        help_text="如2*480GB SSD + 4*2TB HDD"
    )
    raid_card = models.CharField(
        "阵列卡", max_length=255, blank=True, null=True,
        help_text="阵列卡型号"
    )
    raid_config = models.CharField(
        "阵列配置", max_length=255, blank=True, null=True,
        help_text="RAID级别及配置详情"
    )
    hot_spare_disk = models.CharField(
        "热备盘", max_length=255, blank=True, null=True,
        help_text="热备盘信息"
    )
    virtual_disk = models.CharField(
        "虚拟磁盘", max_length=255, blank=True, null=True,
        help_text="虚拟磁盘配置"
    )
    disk_form_factor = models.CharField(
        "硬盘外型", max_length=50, blank=True, null=True,
        help_text="2.5寸/3.5寸"
    )
    disk_media_type = models.CharField(
        "介质类型", max_length=50, blank=True, null=True,
        help_text="SSD/HDD"
    )
    disk_bus_protocol = models.CharField(
        "总线协议", max_length=50, blank=True, null=True,
        help_text="SATA/SAS/NVMe"
    )
    disk_count = models.CharField(
        "硬盘数量", max_length=50, blank=True, null=True
    )
    disk_capacity_per_disk = models.CharField(
        "单盘大小", max_length=100, blank=True, null=True,
        help_text="如1.92TB"
    )
    gpu_name = models.CharField(
        "GPU名称", max_length=255, blank=True, null=True
    )
    gpu_type = models.CharField(
        "GPU类型", max_length=255, blank=True, null=True,
        help_text="如NVIDIA Tesla T4"
    )
    gpu_desc = models.TextField(
        "GPU描述", blank=True, null=True
    )

    # ========== 网络信息 ==========
    onboard_nic_model = models.CharField(
        "板载网卡型号", max_length=255, blank=True, null=True
    )
    onboard_nic_speed = models.CharField(
        "板载网卡速率", max_length=100, blank=True, null=True,
        help_text="如1Gbps、10Gbps"
    )
    onboard_nic_ports = models.CharField(
        "板载网卡接口数量", max_length=50, blank=True, null=True
    )
    additional_nic_model = models.CharField(
        "附加网卡型号", max_length=255, blank=True, null=True
    )
    additional_nic_speed = models.CharField(
        "附加网卡速率", max_length=100, blank=True, null=True
    )
    additional_nic_ports = models.CharField(
        "附加网卡接口数量", max_length=50, blank=True, null=True
    )

    # ========== 软件信息 ==========
    os_name = models.CharField(
        "操作系统名称", max_length=255,
        help_text="如VMware ESXi、CentOS、Windows Server"
    )
    os_version = models.CharField(
        "操作系统版本", max_length=255, blank=True, null=True,
        help_text="详细版本号"
    )
    virtualization_type = models.CharField(
        "虚拟化类型", max_length=100, blank=True, null=True,
        help_text="VMware/KVM/裸金属"
    )
    virtualization_ip = models.CharField(
        "虚拟化IP", max_length=100, blank=True, null=True
    )
    virtualization_address = models.CharField(
        "虚拟化地址", max_length=500, blank=True, null=True,
        help_text="虚拟化平台管理地址"
    )
    virtualization_username = models.CharField(
        "虚拟化用户名", max_length=255, blank=True, null=True
    )
    virtualization_password = models.CharField(
        "虚拟化密码", max_length=255, blank=True, null=True
    )

    # ========== 管理信息 ==========
    management_ip = models.CharField(
        "管理IP", max_length=100, blank=True, null=True,
        help_text="带外管理IP（如iDRAC/IPMI）"
    )
    management_address = models.CharField(
        "管理地址", max_length=500, blank=True, null=True,
        help_text="带外管理Web地址"
    )
    management_username = models.CharField(
        "管理用户名", max_length=255, blank=True, null=True
    )
    management_password = models.CharField(
        "管理密码", max_length=255, blank=True, null=True
    )
    bios_password = models.CharField(
        "BIOS密码", max_length=255, blank=True, null=True
    )
    remote_control = models.CharField(
        "远程控制", max_length=255, blank=True, null=True,
        help_text="远程控制卡类型或状态"
    )
    operator = models.CharField(
        "主要维护人", max_length=100, blank=True, null=True
    )
    bak_operator = models.CharField(
        "备份维护人", max_length=100, blank=True, null=True
    )
    duty_phone = models.CharField(
        "值班电话", max_length=50, blank=True, null=True,
        help_text="紧急联系电话"
    )

    # ========== 系统字段 ==========
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "物理机项目元数据"
        verbose_name_plural = "物理机项目元数据"
        ordering = ['project', 'hostname']
        indexes = [
            models.Index(fields=['hostname']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
            models.Index(fields=['vendor']),
            models.Index(fields=['data_center']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['asset_code']),
        ]

    def __str__(self):
        return f"{self.hostname} ({self.project})"


class ProjectNetworkDevice(models.Model):
    """网络设备项目元数据管理"""

    # 必需字段
    hostname = models.CharField(
        "主机名",
        max_length=255,
        unique=True,
        help_text="唯一标识网络设备的主机名"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="网络设备所属的项目名称"
    )
    environment = models.CharField(
        "环境类型",
        max_length=50,
        help_text="网络设备所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="网络设备的主要负责人"
    )
    management_ip = models.CharField(
        "管理IP",
        max_length=100,
        help_text="网络设备的管理IP地址"
    )
    os_info = models.CharField(
        "操作系统",
        max_length=255,
        blank=True,
        null=True,
        help_text="网络设备操作系统"
    )
    device_type = models.CharField(
        "设备类型",
        max_length=50,
        help_text="网络设备类型"
    )

    # 重要字段
    model = models.CharField(
        "设备型号",
        max_length=255,
        blank=True,
        null=True,
        help_text="网络设备型号"
    )
    serial_number = models.CharField(
        "序列号",
        max_length=255,
        blank=True,
        null=True,
        help_text="设备序列号"
    )
    vendor = models.CharField(
        "厂商",
        max_length=100,
        blank=True,
        null=True,
        help_text="设备厂商"
    )
    software_version = models.CharField(
        "软件版本",
        max_length=255,
        blank=True,
        null=True,
        help_text="操作系统/软件版本"
    )
    location = models.CharField(
        "位置",
        max_length=255,
        blank=True,
        null=True,
        help_text="设备所在位置/机柜"
    )

    # 新增字段：连接方式和连接端口
    connection_method = models.CharField(
        "连接方式",
        max_length=50,
        blank=True,
        null=True,
        help_text="设备连接方式"
    )
    connection_port = models.IntegerField(
        "连接端口",
        blank=True,
        null=True,
        help_text="设备连接端口"
    )

    # 新增POE支持字段
    poe_support = models.CharField(
        "POE支持",
        max_length=50,
        blank=True,
        null=True,
        help_text="设备POE支持类型"
    )

    # 可选字段
    port_count = models.IntegerField(
        "端口数量",
        blank=True,
        null=True,
        help_text="设备端口总数"
    )
    interface_speed = models.CharField(
        "业务接口速率",
        max_length=50,
        blank=True,
        null=True,
        help_text="业务接口速率"
    )
    uplink_device = models.CharField(
        "上联设备",
        max_length=255,
        blank=True,
        null=True,
        help_text="上联设备名称"
    )
    mac_address = models.CharField(
        "MAC地址",
        max_length=50,
        blank=True,
        null=True
    )
    asset_tag = models.CharField(
        "资产标签",
        max_length=255,
        blank=True,
        null=True
    )
    purchase_date = models.DateField(
        "采购日期",
        blank=True,
        null=True
    )
    status = models.CharField(
        "状态",
        max_length=50,
        blank=True,
        null=True,
        help_text="设备状态"
    )
    warranty_expire = models.DateField(
        "维保到期",
        blank=True,
        null=True
    )
    description = models.TextField(
        "备注",
        blank=True,
        null=True,
        help_text="附加说明信息"
    )

    # 时间戳
    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True
    )

    class Meta:
        verbose_name = "网络设备项目元数据"
        verbose_name_plural = "网络设备项目元数据"
        ordering = ['project', 'hostname']
        indexes = [
            models.Index(fields=['hostname']),
            models.Index(fields=['management_ip']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
            models.Index(fields=['device_type']),
            models.Index(fields=['vendor']),
            models.Index(fields=['poe_support']),
        ]

    def __str__(self):
        return f"{self.hostname} ({self.management_ip})"


class ProjectVMware(models.Model):
    """VMware虚拟机项目元数据管理"""
    hostname = models.CharField(
        "主机名",
        max_length=255,
        unique=True,
        help_text="唯一标识虚拟机的主机名"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="虚拟机所属的项目名称"
    )
    environment = models.CharField(
        "环境类型",
        max_length=50,
        choices=(
            ('prod', '生产环境'),
            ('test', '测试环境'),
            ('dev', '开发环境'),
            ('uat', '用户验收环境'),
            ('stg', '预生产环境'),
            ('dr', '灾备环境'),
            ('other', '其他')
        ),
        default='prod',
        help_text="虚拟机所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="虚拟机的主要负责人"
    )
    department = models.CharField(
        "部门",
        max_length=100,
        blank=True,
        null=True,
        help_text="负责人所属部门"
    )
    description = models.TextField(
        "说明",
        blank=True,
        null=True,
        help_text="虚拟机详细说明"
    )
    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True
    )

    class Meta:
        verbose_name = "VMware虚拟机项目元数据"
        verbose_name_plural = "VMware虚拟机项目元数据"
        ordering = ['project', 'hostname']
        indexes = [
            models.Index(fields=['hostname']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.hostname} ({self.project})"


class ProjectProxmox(models.Model):
    """Proxmox虚拟机项目元数据管理"""
    hostname = models.CharField(
        "主机名",
        max_length=255,
        unique=True,
        help_text="唯一标识虚拟机的主机名"
    )
    vmid = models.CharField(
        "VMID",
        max_length=50,
        unique=True,
        help_text="Proxmox虚拟机ID"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="虚拟机所属的项目名称"
    )
    environment = models.CharField(
        "环境类型",
        max_length=50,
        choices=(
            ('prod', '生产环境'),
            ('test', '测试环境'),
            ('dev', '开发环境'),
            ('uat', '用户验收环境'),
            ('stg', '预生产环境'),
            ('dr', '灾备环境'),
            ('other', '其他')
        ),
        default='prod',
        help_text="虚拟机所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="虚拟机的主要负责人"
    )
    department = models.CharField(
        "部门",
        max_length=100,
        blank=True,
        null=True,
        help_text="负责人所属部门"
    )
    description = models.TextField(
        "说明",
        blank=True,
        null=True,
        help_text="虚拟机描述信息"
    )
    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True
    )

    class Meta:
        verbose_name = "Proxmox虚拟机项目元数据"
        verbose_name_plural = "Proxmox虚拟机项目元数据"
        ordering = ['project', 'hostname']
        indexes = [
            models.Index(fields=['hostname']),
            models.Index(fields=['vmid']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.hostname} (VMID: {self.vmid})"


class ProxmoxVM(models.Model):
    """Proxmox VE 虚拟机资产"""
    
    class StatusChoices(models.TextChoices):
        RUNNING = 'running', _('运行中')
        STOPPED = 'stopped', _('已停止')
        PAUSED = 'paused', _('已暂停')
    
    class HAStateChoices(models.TextChoices):
        STARTED = 'started', _('已启动')
        STOPPED = 'stopped', _('已停止')
        ERROR = 'error', _('错误')
        DISABLED = 'disabled', _('已禁用')
    
    class BIOSTypeChoices(models.TextChoices):
        SEABIOS = 'seabios', _('SeaBIOS')
        OVMF = 'ovmf', _('UEFI(OVMF)')
    
    # 唯一标识
    vmid = models.CharField(
        _('VMID'),
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Proxmox虚拟机ID"
    )
    
    # 集群信息
    node = models.CharField(
        _('节点'),
        max_length=100,
        help_text="所在PVE节点"
    )
    cluster = models.CharField(
        _('集群'),
        max_length=100,
        blank=True,
        default='',
        help_text="集群名称"
    )
    pool = models.CharField(
        _('资源池'),
        max_length=100,
        blank=True,
        default='',
        help_text="资源池名称"
    )
    
    # 基础信息
    name = models.CharField(_('虚拟机名称'), max_length=255)
    status = models.CharField(
        _('运行状态'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.STOPPED
    )
    template = models.BooleanField(
        _('是否为模板'),
        default=False
    )
    
    # 硬件配置
    cpu_cores = models.PositiveIntegerField(_('CPU核心数'), default=1)
    cpu_sockets = models.PositiveIntegerField(_('CPU插槽数'), default=1)
    memory_mb = models.PositiveIntegerField(_('内存(MB)'), default=512)
    boot_disk_gb = models.FloatField(
        _('引导磁盘大小(GB)'),
        default=0,
        help_text="引导磁盘大小"
    )
    total_disk_gb = models.FloatField(
        _('磁盘总大小(GB)'),
        default=0,
        help_text="所有磁盘总大小"
    )
    bios_type = models.CharField(
        _('BIOS类型'),
        max_length=20,
        choices=BIOSTypeChoices.choices,
        default=BIOSTypeChoices.SEABIOS
    )
    
    # 网络信息
    ip_address = models.CharField(
        _('IP地址'),
        max_length=100,
        blank=True,
        default='',
        help_text="虚拟机IP地址"
    )
    mac_address = models.CharField(
        _('MAC地址'),
        max_length=50,
        blank=True,
        default=''
    )
    
    # 系统信息
    os_type = models.CharField(
        _('操作系统类型'),
        max_length=100,
        blank=True,
        default='',
        help_text="如: l26(Linux 2.6+), win10等"
    )
    uptime = models.BigIntegerField(
        _('运行时间(秒)'),
        default=0
    )
    
    # 高可用配置
    ha_state = models.CharField(
        _('高可用状态'),
        max_length=20,
        choices=HAStateChoices.choices,
        blank=True,
        default='',
        help_text="HA状态"
    )
    ha_group = models.CharField(
        _('高可用组'),
        max_length=100,
        blank=True,
        default=''
    )
    
    # Guest Agent
    agent_enabled = models.BooleanField(
        _('Guest Agent已启用'),
        default=False
    )
    agent_running = models.BooleanField(
        _('Guest Agent运行中'),
        default=False
    )
    
    # 备份信息
    last_backup = models.DateTimeField(
        _('最后备份时间'),
        null=True,
        blank=True
    )
    # 备份存储
    backup_storage = models.CharField(
        _('备份存储'),
        max_length=100,
        blank=True,
        default='',
        help_text="最后备份所在的存储名称，如 pbsbj, local-backup"
    )

    # 备份卷ID（完整路径）
    last_backup_volid = models.CharField(
        _('最后备份卷ID'),
        max_length=255,
        blank=True,
        default='',
        help_text="如: pbsbj:backup/vm/1013/2026-03-05T13:00:36Z"
    )

    # 备份大小（字节）
    last_backup_size = models.BigIntegerField(
        _('最后备份大小'),
        default=0,
        help_text="备份文件大小（字节）"
    )

    # 备份格式
    last_backup_format = models.CharField(
        _('备份格式'),
        max_length=50,
        blank=True,
        default='',
        help_text="如: pbs-vm, vma.zst, vma.lzo"
    )

    # 备份状态/验证状态
    last_backup_status = models.CharField(
        _('备份验证状态'),
        max_length=20,
        blank=True,
        default='',
        help_text="ok, failed, pending"
    )

    # 备份数量统计
    backup_count = models.PositiveIntegerField(
        _('备份数量'),
        default=0,
        help_text="该VM的历史备份总数"
    )

    # 备份历史记录（JSON）
    backup_history = models.JSONField(
        _('备份历史'),
        default=list,
        help_text="最近5个备份记录列表，用于展示趋势"
    )

    # 保留旧字段（兼容）
    backup_mode = models.CharField(
        _('备份模式'),
        max_length=50,
        blank=True,
        default='',
        help_text="snapshot/suspend/stop（vzdump参数）"
    )
    
    # 存储信息
    storage = models.CharField(
        _('主存储池'),
        max_length=100,
        blank=True,
        default=''
    )
    disk_info = models.JSONField(
        _('磁盘详情'),
        default=list,
        help_text="磁盘详细信息JSON"
    )
    
    # 项目关联（从ProjectProxmox同步）
    project_name = models.CharField(
        _('所属项目'),
        max_length=255,
        blank=True,
        default='未分配'
    )
    environment_type = models.CharField(
        _('环境类型'),
        max_length=50,
        blank=True,
        default='未分类'
    )
    owner = models.CharField(
        _('负责人'),
        max_length=100,
        blank=True,
        default='系统管理员'
    )
    description = models.TextField(
        _('描述'),
        blank=True,
        default=''
    )
    
    # 元数据
    last_sync = models.DateTimeField(
        _('最后同步时间'),
        default=timezone.now
    )
    created_at = models.DateTimeField(
        _('创建时间'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Proxmox虚拟机')
        verbose_name_plural = _('Proxmox虚拟机')
        ordering = ['-last_sync']
        indexes = [
            models.Index(fields=['vmid']),
            models.Index(fields=['node']),
            models.Index(fields=['cluster']),
            models.Index(fields=['status']),
            models.Index(fields=['environment_type']),
            models.Index(fields=['ha_state']),
        ]
    
    def __str__(self):
        return f"{self.name} (VMID: {self.vmid})"
    
    @property
    def memory_gb(self):
        """内存GB显示值"""
        return round(self.memory_mb / 1024, 2)
    
    @property
    def formatted_uptime(self):
        """格式化的运行时间"""
        if self.uptime <= 0:
            return _("未运行")
        days = self.uptime // 86400
        hours = (self.uptime % 86400) // 3600
        minutes = (self.uptime % 3600) // 60
        if days > 0:
            return f"{days}天{hours}小时"
        elif hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
    
    def get_status_display_cn(self):
        """获取中文状态显示"""
        return dict(self.StatusChoices.choices).get(self.status, _('未知状态'))
    
    def get_ha_state_display_cn(self):
        """获取中文HA状态显示"""
        if not self.ha_state:
            return _('未启用')
        return dict(self.HAStateChoices.choices).get(self.ha_state, self.ha_state)
    
    @property
    def is_backup_healthy(self):
        """检查备份是否健康（30天内有备份）"""
        if not self.last_backup:
            return False
        days_since_backup = (timezone.now() - self.last_backup).days
        return days_since_backup <= 30

    @property
    def last_backup_size_gb(self):
        """备份大小（GB显示）"""
        if self.last_backup_size:
            return round(self.last_backup_size / (1024 ** 3), 2)
        return 0

    @property
    def is_backup_healthy(self):
        """检查备份是否健康（30天内有备份且验证通过）"""
        if not self.last_backup:
            return False
        days_since = (timezone.now() - self.last_backup).days
        return days_since <= 30 and self.last_backup_status in ['ok', '']

    @property
    def backup_health_status(self):
        """备份健康状态（用于前端标签）"""
        if not self.last_backup:
            return 'none'  # 无备份
        days_since = (timezone.now() - self.last_backup).days
        if days_since > 30:
            return 'expired'  # 过期
        if self.last_backup_status == 'failed':
            return 'failed'  # 验证失败
        if self.backup_count < 3:
            return 'warning'  # 备份数量少
        return 'healthy'  # 健康

    def get_backup_trend(self):
        """获取备份趋势（最近7天是否有备份）"""
        if not self.backup_history:
            return []

        trend = []
        for backup in self.backup_history[:7]:
            trend.append({
                'date': datetime.fromtimestamp(backup.get('ctime', 0)).strftime('%m-%d'),
                'size_gb': round(backup.get('size', 0) / (1024 ** 3), 1)
            })
        return trend



