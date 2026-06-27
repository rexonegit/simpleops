# aliyun/models.py
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django.core.exceptions import ValidationError

class AliyunOSS(models.Model):
    name = models.CharField("Bucket名称", max_length=255, primary_key=True)
    region = models.CharField("地域", max_length=50)
    storage_class = models.CharField("存储类型", max_length=50)
    creation_date = models.DateTimeField("创建时间")
    redundancy_type = models.CharField("冗余类型", max_length=50)
    versioning = models.CharField(
        "版本控制",
        max_length=20,
        choices=(('Enabled', '已开启'), ('Disabled', '未开启'), ('Suspended', '已暂停')),
        default='Disabled',  # 添加默认值
        null=True,  # 允许为空
        blank=True
    )
    transfer_acceleration = models.CharField(
        "传输加速",
        max_length=20,
        choices=(('Enabled', '已开启'), ('Disabled', '未开启')),
        default='Disabled',  # 添加默认值
        null=True,  # 允许为空
        blank=True
    )
    storage = models.BigIntegerField("容量", default=0)  # 单位：字节
    standard_storage = models.BigIntegerField("标准型存储量", default=0)
    standard_object_count = models.BigIntegerField(default=0, verbose_name="标准存储对象数量")
    ia_storage = models.BigIntegerField("低频型计费存储量", default=0)
    archive_storage = models.BigIntegerField("归档型计费存储量", default=0)
    cold_archive_storage = models.BigIntegerField("冷归档型计费存储量", default=0)
    deep_cold_archive_storage = models.BigIntegerField("深度冷归档型计费存储量", default=0)
    monthly_flow = models.BigIntegerField("当月流量", default=0)  # 单位：字节
    monthly_access_count = models.IntegerField("当月访问次数", default=0)
    tags = models.JSONField("Bucket标签", default=dict)

    # 修复：添加默认值
    acl = models.CharField(
        "读写权限",
        max_length=20,
        choices=(
            ('private', '私有'),
            ('public-read', '公共读'),
            ('public-read-write', '公共读写')
        ),
        default='private'
    )

    # 新增字段
    access_monitor = models.CharField(
        "访问跟踪",
        max_length=20,
        choices=(('Enabled', '已开启'), ('Disabled', '未开启')),
        default='Disabled',  # 添加默认值
        null=True,  # 允许为空
        blank=True
    )
    data_redundancy_type = models.CharField("数据冗余类型", max_length=50, null=True, blank=True)
    owner_id = models.CharField("拥有者ID", max_length=255, null=True, blank=True)
    owner_display_name = models.CharField("拥有者名称", max_length=255, null=True, blank=True)
    resource_group_id = models.CharField("资源组ID", max_length=255, null=True, blank=True)
    sse_algorithm = models.CharField("加密算法", max_length=50, null=True, blank=True)
    kms_master_key_id = models.CharField("KMS密钥ID", max_length=255, null=True, blank=True)
    kms_data_encryption = models.CharField("KMS数据加密", max_length=50, null=True, blank=True)
    cross_region_replication = models.CharField(
        "跨区域复制",
        max_length=20,
        choices=(('Enabled', '已开启'), ('Disabled', '未开启')),
        default='Disabled',  # 添加默认值
        null=True,  # 允许为空
        blank=True
    )
    log_bucket = models.CharField("日志存储Bucket", max_length=255, null=True, blank=True)
    log_prefix = models.CharField("日志前缀", max_length=255, null=True, blank=True)
    comment = models.TextField("备注", null=True, blank=True)
    block_public_access = models.CharField(
        "禁止公共访问",
        max_length=20,
        choices=(('Enabled', '已开启'), ('Disabled', '未开启')),
        default='Disabled',  # 添加默认值
        null=True,  # 允许为空
        blank=True
    )
    archive_direct_read = models.CharField(
        "归档直读",
        max_length=20,
        choices=(('Enabled', '已开启'), ('Disabled', '未开启')),
        default='Disabled',  # 添加默认值
        null=True,  # 允许为空
        blank=True
    )
    tls_version = models.CharField("允许的TLS版本", max_length=50, null=True, blank=True)
    extranet_endpoint = models.CharField("外网Endpoint", max_length=255)
    intranet_endpoint = models.CharField("内网Endpoint", max_length=255)
    object_count = models.BigIntegerField("文件数量", default=0)
    fragments = models.IntegerField("文件碎片", default=0)
    multipart_uploads = models.IntegerField("Multipart Upload数", default=0)
    storage_growth = models.FloatField("月同比", default=0.0)  # 百分比
    account_name = models.CharField("所属账号", max_length=100)
    # 新增统计字段
    multipart_upload_count = models.BigIntegerField("Multipart Upload数", default=0)
    infrequent_access_storage = models.BigIntegerField("低频存储计费量", default=0)
    infrequent_access_real_storage = models.BigIntegerField("低频存储实际量", default=0)
    infrequent_access_object_count = models.BigIntegerField("低频存储对象数", default=0)
    archive_real_storage = models.BigIntegerField("归档存储实际量", default=0)
    archive_object_count = models.BigIntegerField("归档存储对象数", default=0)
    cold_archive_real_storage = models.BigIntegerField("冷归档存储实际量", default=0)
    cold_archive_object_count = models.BigIntegerField("冷归档存储对象数", default=0)
    deep_cold_archive_real_storage = models.BigIntegerField("深度冷归档实际量", default=0)
    deep_cold_archive_object_count = models.BigIntegerField("深度冷归档对象数", default=0)
    last_modified_time = models.BigIntegerField("最后修改时间", default=0)
    live_channel_count = models.BigIntegerField("直播通道数", default=0)
    delete_marker_count = models.BigIntegerField("删除标记数", default=0)

    class Meta:
        verbose_name = "阿里云OSS Bucket"
        verbose_name_plural = "阿里云OSS Bucket"
        ordering = ['-creation_date']

class AliyunRAMUser(models.Model):
    """阿里云RAM用户模型"""
    user_id = models.CharField("用户ID", max_length=128, primary_key=True)
    user_name = models.CharField("用户名", max_length=128)
    user_principal_name = models.CharField("用户登录名称", max_length=255, null=True, blank=True)
    display_name = models.CharField("显示名称", max_length=128, null=True, blank=True)
    account_name = models.CharField("所属主账号", max_length=128)
    email = models.EmailField("邮箱", null=True, blank=True)
    mobile_phone = models.CharField("手机号", max_length=20, null=True, blank=True)
    comments = models.TextField("备注", null=True, blank=True)
    create_date = models.DateTimeField("创建时间")
    update_date = models.DateTimeField("更新时间")
    last_login_date = models.DateTimeField("最后登录时间", null=True, blank=True)

    # 状态字段
    status = models.CharField("用户状态", max_length=20, default="active")
    active = models.BooleanField("是否激活", default=True)
    provision_type = models.CharField("同步类型", max_length=20, default="Manual")

    # MFA相关
    mfa_enabled = models.BooleanField("MFA启用状态", default=False)

    # 访问密钥相关
    access_keys_count = models.IntegerField("访问密钥数量", default=0)
    access_keys = models.JSONField("访问密钥详情", default=list)

    # 权限策略相关
    attached_policies = models.JSONField("附加策略", default=list)

    # 用户组相关
    groups = models.JSONField("所属用户组", default=list)

    # 标签信息
    tags = models.JSONField("标签", default=list)

    console_status = models.CharField(
        "控制台访问状态",
        max_length=20,
        default='未开启',
        choices=(
            ('未开启', '未开启'),
            ('已开启', '已开启'),
            ('已禁用', '已禁用'),
            ('未知状态', '未知状态')
        )
    )


    created_at = models.DateTimeField("记录创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("记录更新时间", auto_now=True)

    class Meta:
        verbose_name = "阿里云RAM用户"
        verbose_name_plural = "阿里云RAM用户"
        ordering = ['-update_date']
        indexes = [
            models.Index(fields=['user_name']),
            models.Index(fields=['user_principal_name']),
            models.Index(fields=['account_name']),
            models.Index(fields=['status']),
            models.Index(fields=['create_date']),
        ]

    def __str__(self):
        return f"{self.user_name} ({self.display_name or '无显示名'})"


def validate_disk_structure(value):
    """验证系统盘结构"""
    required_keys = ['device', 'category', 'size']
    if not all(key in value for key in required_keys):
        raise ValidationError(f"系统盘结构不完整，必须包含 {required_keys} 字段")


class AliyunECS(models.Model):
    id = models.AutoField(primary_key=True)
    instance_id = models.CharField("实例ID", max_length=255)
    account_name = models.CharField("所属账号", max_length=255, null=True, blank=True)
    instance_name = models.CharField("实例名称", max_length=255, null=True, blank=True)
    hostname = models.CharField("主机名", max_length=255, null=True, blank=True)
    osname = models.TextField("操作系统", null=True, blank=True)
    status = models.CharField("状态", max_length=50, null=True, blank=True)
    description = models.TextField("描述", null=True, blank=True)
    region = models.CharField("地域", max_length=100, null=True, blank=True)
    zone = models.CharField("可用区", max_length=100, null=True, blank=True)
    public_ip = models.CharField("公网IP", max_length=100, null=True, blank=True)
    private_ip = models.CharField("私网IP", max_length=100, null=True, blank=True)
    eip = models.CharField("弹性IP", max_length=100, null=True, blank=True)
    ipv6 = models.CharField("IPv6", max_length=100, null=True, blank=True)
    cpu = models.IntegerField("CPU", null=True, blank=True)
    memory = models.IntegerField("内存(MB)", null=True, blank=True)
    payment_type = models.CharField("付费类型", max_length=50, null=True, blank=True)
    network_type = models.CharField("网络类型", max_length=50, null=True, blank=True)
    vpc_attributes = JSONField("专有网络属性", null=True, blank=True)
    bandwidth = models.IntegerField("带宽(Mbps)", null=True, blank=True)
    bandwidth_charge_mode = models.CharField("带宽计费方式", max_length=50, null=True, blank=True)
    creation_time = models.DateTimeField("创建时间", null=True, blank=True)
    expire_time = models.DateTimeField("到期时间", null=True, blank=True)
    tags = JSONField("标签", default=dict)
    instance_type = models.CharField("实例规格", max_length=100, null=True, blank=True)
    instance_family = models.CharField("实例规格族", max_length=100, null=True, blank=True)
    image_id = models.CharField("镜像ID", max_length=255, null=True, blank=True)
    resource_group_id = models.CharField("资源组ID", max_length=255, null=True, blank=True)
    system_disk = models.JSONField("系统盘", default=dict, validators=[validate_disk_structure])
    data_disks = models.JSONField("数据盘", default=list)


    def format_system_disk(self):
        """系统盘显示格式化（增强容错）"""
        try:
            disk = self.system_disk
            if not isinstance(disk, dict):
                return "无效的系统盘数据"

            category_map = {
                'cloud_essd': 'ESSD云盘',
                'cloud_ssd': 'SSD云盘',
                'cloud_efficiency': '高效云盘',
                'cloud': '普通云盘'
            }

            return (
                f"{category_map.get(disk.get('category', 'cloud_essd'))} "
                f"{disk.get('performance_level', 'PL0')} "
                f"{disk.get('size', '0GiB')} "
                f"({disk.get('iops', 0)} IOPS)"
            )
        except Exception as e:
            return f"系统盘信息解析错误: {str(e)}"

    def format_data_disks(self):
        """数据盘显示格式化（增强容错）"""
        try:
            disks = []
            category_map = {
                'cloud_essd': 'ESSD云盘',
                'cloud_ssd': 'SSD云盘',
                'cloud_efficiency': '高效云盘'
            }

            for disk in self.data_disks:
                disks.append(
                    f"数据盘{disk.get('device', '未知')}："
                    f"{category_map.get(disk.get('category', '未知类型'))} "
                    f"{disk.get('performance_level', '')} "
                    f"{disk.get('size', '0GiB')} "
                    f"({disk.get('iops', 0)} IOPS)"
                )
            return "<br>".join(disks) if disks else "无数据盘"
        except Exception as e:
            return f"数据盘信息解析错误: {str(e)}"

    # 修改为 JSONField 存储多个安全组 ID
    security_group_ids = models.JSONField(
            "安全组ID列表",
            default=list,
            help_text="关联的安全组ID列表"
        )
    vpc_id = models.CharField("专有网络ID", max_length=255, null=True, blank=True)
    vswitch_id = models.CharField("交换机ID", max_length=255, null=True, blank=True)
    stopped_mode = models.CharField("停机模式", max_length=50, null=True, blank=True)
    release_protection = models.BooleanField("实例释放保护", default=False)
    gpu_type = models.CharField("GPU类型", max_length=100, null=True, blank=True)
    gpu_count = models.IntegerField("GPU数量", null=True, blank=True)
    key_pair = models.CharField("密钥对", max_length=255, null=True, blank=True)
    project = models.CharField("所属项目", max_length=255, null=True, blank=True)
    environment = models.CharField("环境类型", max_length=50, null=True, blank=True)
    owner = models.CharField("负责人", max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-creation_time']


class ProjectAliyunecs(models.Model):
    """阿里云资源项目元数据管理"""
    lookup_field = 'id'
    hostname = models.CharField(
        "主机名",
        max_length=255,
        unique=True,
        help_text="唯一标识资源的主机名"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="资源所属的项目名称"
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
        help_text="资源所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="资源的主要负责人"
    )
    department = models.CharField(
        "所属部门",
        max_length=100,
        blank=True,
        null=True,
        help_text="资源所属的部门"
    )
    business_unit = models.CharField(
        "业务单元",
        max_length=100,
        blank=True,
        null=True,
        help_text="资源所属的业务单元"
    )
    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True
    )
    notes = models.TextField(
        "备注",
        blank=True,
        null=True,
        help_text="附加说明信息"
    )

    class Meta:
        verbose_name = "阿里云项目元数据"
        verbose_name_plural = "阿里云项目元数据"
        ordering = ['project', 'hostname']
        indexes = [
            models.Index(fields=['hostname']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.hostname} ({self.project})"


class AliyunDomain(models.Model):
    STATUS_CHOICES = (
        ('ok', '正常'),
        ('clientHold', '暂停解析'),
        ('serverHold', '注册局锁定'),
        ('inactive', '未激活'),
    )

    domain_name = models.CharField('域名', max_length=255, unique=True)
    account_name = models.CharField('所属账号', max_length=100)
    registration_date = models.DateTimeField('注册时间')
    expiration_date = models.DateTimeField('到期时间')
    domain_status = models.CharField('状态', max_length=255, choices=STATUS_CHOICES)
    dns_server = models.TextField('DNS服务器')
    registrant_type = models.CharField('注册类型', max_length=50)
    registrant_organization = models.CharField('注册组织', max_length=255)
    registrant = models.CharField('注册人', max_length=100)
    email = models.EmailField('联系邮箱')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)


    class Meta:
        verbose_name = '阿里云域名'
        verbose_name_plural = '阿里云域名'

    def __str__(self):
        return self.domain_name

class AliyunDNSRecord(models.Model):
    domain = models.ForeignKey(
        'AliyunDomain',
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='所属域名'  # 添加明确的中文标签
    )
    domain_name = models.CharField(max_length=255)  # 冗余字段用于查询
    complete_domain = models.CharField('完整域名', max_length=255, editable=False)
    is_auto = models.BooleanField(default=True, verbose_name="自动同步记录")
    record_id = models.CharField(max_length=255, unique=True, verbose_name="记录ID")
    type = models.CharField('类型', max_length=10)  # A, CNAME, MX 等
    rr = models.CharField('主机记录', max_length=190)
    value = models.CharField('记录值', max_length=190)
    ttl = models.PositiveIntegerField('TTL')
    status = models.CharField('状态', max_length=10)
    line = models.CharField('解析线路', max_length=50)
    locked = models.BooleanField('锁定状态')
    weight = models.PositiveIntegerField('权重', null=True)
    remark = models.CharField(max_length=255, null=True, blank=True, default='')
    create_timestamp = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    update_timestamp = models.DateTimeField(null=True, blank=True, verbose_name="更新时间")
    project = models.CharField(
        "所属项目",
        max_length=255,
        null=True,
        blank=True,
        help_text="从CSV同步的所属项目信息"
    )

    environment = models.CharField(
        "环境类型",
        max_length=50,
        null=True,
        blank=True,
        choices=(('prod', '生产环境'), ('test', '测试环境'), ('dev', '开发环境')),
        help_text="从CSV同步的环境分类"
    )

    owner = models.CharField(
        "负责人",
        max_length=100,
        null=True,
        blank=True,
        help_text="从CSV同步的责任人信息"
    )


    class Meta:
        indexes = [
            models.Index(fields=['complete_domain']),
        ]

    def save(self, *args, **kwargs):
        """增强保存逻辑，自动维护domain_name字段"""
        # 确保domain关系存在
        if not self.domain_id:
            raise ValueError("DNS记录必须关联到域名对象")

        # 自动同步domain_name（从关联的域名获取）
        self.domain_name = self.domain.domain_name  # 新增此行

        # 生成complete_domain
        if self.rr == '@':
            self.complete_domain = self.domain.domain_name
        else:
            self.complete_domain = f"{self.rr}.{self.domain.domain_name}".rstrip('.')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rr}.{self.domain.domain_name}"


class ProjectAliyunDomain(models.Model):
    """阿里云域名解析记录项目元数据管理"""
    complete_domain = models.CharField(
        "完整域名",
        max_length=255,
        unique=True,
        help_text="完整的域名记录（如：www.example.com）"
    )
    type = models.CharField(
        "记录类型",
        max_length=10,
        choices=(
            ('A', 'A记录'),
            ('CNAME', 'CNAME记录'),
            ('MX', 'MX记录'),
            ('TXT', 'TXT记录'),
            ('NS', 'NS记录'),
            ('SRV', 'SRV记录'),
            ('AAAA', 'AAAA记录'),
            ('CAA', 'CAA记录')
        ),
        default='A',
        help_text="DNS记录类型"
    )
    rr = models.CharField(
        "主机记录",
        max_length=190,
        help_text="域名前缀（如：www）"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="域名记录所属的项目名称"
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
        help_text="域名记录所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="域名记录的主要负责人"
    )
    description = models.TextField(
        "描述",
        blank=True,
        null=True,
        help_text="域名记录的用途描述"
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
        verbose_name = "阿里云域名解析记录元数据"
        verbose_name_plural = "阿里云域名解析记录元数据"
        ordering = ['project', 'complete_domain']
        indexes = [
            models.Index(fields=['complete_domain']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.complete_domain} ({self.type})"


class AliyunSLB(models.Model):
    load_balancer_id = models.CharField("负载均衡 ID", max_length=64, primary_key=True)
    load_balancer_name = models.CharField("名称", max_length=255)
    region_id = models.CharField("地域", max_length=30)
    address = models.GenericIPAddressField("服务地址")
    address_type = models.CharField("地址类型", max_length=20, choices=(('internet', '公网'), ('intranet', '内网')))
    network_type = models.CharField("网络类型", max_length=20, choices=(('vpc', '专有网络'), ('classic', '经典网络')))
    vpc_id = models.CharField("VPC ID", max_length=64, blank=True, null=True)
    vswitch_id = models.CharField("VSwitch ID", max_length=64, blank=True, null=True)
    load_balancer_spec = models.CharField("规格", max_length=30, blank=True, null=True)
    status = models.CharField("状态", max_length=20, choices=(('active', '运行中'), ('inactive', '已停止')))
    creation_time = models.DateTimeField("创建时间")
    account_name = models.CharField("所属账号", max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 新增字段
    bandwidth = models.IntegerField("带宽峰值", default=0)
    internet_charge_type = models.CharField("计费类型", max_length=50, null=True, blank=True)
    master_zone_id = models.CharField("主可用区", max_length=50, null=True, blank=True)
    slave_zone_id = models.CharField("备可用区", max_length=50, null=True, blank=True)
    resource_group_id = models.CharField("资源组ID", max_length=255, null=True, blank=True)
    pay_type = models.CharField("付费类型", max_length=20, choices=(('PrePay', '包年包月'), ('PostPay', '按量付费')))
    delete_protection = models.CharField(
        "删除保护",
        max_length=20,
        choices=(('on', '开启'), ('off', '关闭')),
        default='off',
        null=True,  # 允许数据库存储 NULL
        blank=True  # 允许表单验证为空
    )
    listener_ports = models.JSONField("监听端口列表", default=list)
    backend_servers = models.JSONField("后端服务器", default=list)
    tags = models.JSONField("标签", default=dict)
    monthly_flow = models.BigIntegerField("当月流量(Byte)", default=0)
    monthly_requests = models.BigIntegerField("当月请求数", default=0)
    health_status = models.CharField("健康状态", max_length=20, choices=(('normal', '正常'), ('abnormal', '异常')),
                                     default='normal')
    # 项目归属信息（从 ProjectAliyunSLB 同步）
    project = models.CharField('所属项目', max_length=255, null=True, blank=True)
    environment = models.CharField('环境类型', max_length=50, null=True, blank=True)
    owner = models.CharField('负责人', max_length=100, null=True, blank=True)
    remark = models.TextField('说明', null=True, blank=True)

    class Meta:
        verbose_name = "阿里云SLB"
        verbose_name_plural = "阿里云SLB"
        ordering = ['-updated_at']

class AliyunRDS(models.Model):
    DB_ENGINE_CHOICES = [
        ('MySQL', 'MySQL'),
        ('SQLServer', 'SQL Server'),
        ('PostgreSQL', 'PostgreSQL'),
        ('MariaDB', 'MariaDB'),
        ('PPAS', 'PPAS'),
    ]

    PAY_TYPE_CHOICES = [
        ('Prepaid', '包年包月'),
        ('Postpaid', '按量付费'),
    ]

    INSTANCE_TYPE_CHOICES = [
        ('Primary', '主实例'),
        ('Readonly', '只读实例'),
        ('Guard', '灾备实例'),
        ('Temp', '临时实例'),
    ]

    instance_id = models.CharField('实例ID', max_length=128, primary_key=True)
    instance_name = models.CharField('实例名称', max_length=128)
    account_name = models.CharField('所属账号', max_length=64)
    region_id = models.CharField('地域ID', max_length=32)
    engine = models.CharField('数据库引擎', max_length=20, choices=DB_ENGINE_CHOICES)
    engine_version = models.CharField('引擎版本', max_length=32)
    instance_type = models.CharField('实例类型', max_length=20, choices=INSTANCE_TYPE_CHOICES)
    instance_class = models.CharField('规格类型', max_length=64)
    storage = models.IntegerField('存储空间(GB)')
    memory = models.IntegerField('内存大小(GB)')
    cpu = models.IntegerField('CPU核心数')
    connection_string = models.CharField('连接地址', max_length=128)
    port = models.IntegerField('端口号')
    vpc_id = models.CharField('VPC ID', max_length=128, blank=True, null=True)
    vswitch_id = models.CharField('交换机ID', max_length=128, blank=True, null=True)
    security_ips = models.TextField('白名单IP', blank=True, null=True)
    pay_type = models.CharField('付费类型', max_length=20, choices=PAY_TYPE_CHOICES)
    creation_time = models.DateTimeField(null=True, blank=True, default=None)
    expire_time = models.DateTimeField('过期时间', blank=True, null=True)
    status = models.CharField('状态', max_length=32)
    zone_id = models.CharField('可用区', max_length=32)
    connection_mode = models.CharField('连接模式', max_length=32, default='Standard')
    read_only_instances = models.JSONField('只读实例', default=list)
    tags = models.JSONField('标签', default=dict)
    monthly_traffic = models.IntegerField('当月流量(GB)', default=0)
    monthly_requests = models.IntegerField('当月请求数', default=0)
    # 项目归属信息（从 ProjectAliyunRDS 同步）
    project = models.CharField('所属项目', max_length=255, null=True, blank=True)
    environment = models.CharField('环境类型', max_length=50, null=True, blank=True)
    owner = models.CharField('负责人', max_length=100, null=True, blank=True)
    description = models.TextField('说明', null=True, blank=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '阿里云RDS实例'
        verbose_name_plural = '阿里云RDS实例'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.instance_name} ({self.instance_id})"


class ProjectAliyunRDS(models.Model):
    """阿里云RDS项目元数据管理"""
    lookup_field = 'id'
    instance_name = models.CharField(
        "实例名称",
        max_length=128,
        unique=True,
        help_text="唯一标识RDS实例的名称"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="RDS实例所属的项目名称"
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
        help_text="RDS实例所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="RDS实例的主要负责人"
    )
    department = models.CharField(
        "所属部门",
        max_length=100,
        blank=True,
        null=True,
        help_text="RDS实例所属的部门"
    )
    business_unit = models.CharField(
        "业务单元",
        max_length=100,
        blank=True,
        null=True,
        help_text="RDS实例所属的业务单元"
    )
    description = models.TextField(
        "说明",
        blank=True,
        null=True,
        help_text="RDS实例的详细说明"
    )
    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True
    )
    notes = models.TextField(
        "备注",
        blank=True,
        null=True,
        help_text="附加说明信息"
    )

    class Meta:
        verbose_name = "阿里云RDS项目元数据"
        verbose_name_plural = "阿里云RDS项目元数据"
        ordering = ['project', 'instance_name']
        indexes = [
            models.Index(fields=['instance_name']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.instance_name} ({self.project})"


class ProjectAliyunSLB(models.Model):
    """阿里云SLB项目元数据管理"""
    lookup_field = 'id'
    load_balancer_name = models.CharField(
        "负载均衡器名称",
        max_length=255,
        unique=True,
        help_text="唯一标识SLB实例的名称"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="SLB实例所属的项目名称"
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
        help_text="SLB实例所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="SLB实例的主要负责人"
    )
    description = models.TextField(
        "说明",
        blank=True,
        null=True,
        help_text="SLB实例的详细说明"
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
        verbose_name = "阿里云SLB项目元数据"
        verbose_name_plural = "阿里云SLB项目元数据"
        ordering = ['project', 'load_balancer_name']
        indexes = [
            models.Index(fields=['load_balancer_name']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.load_balancer_name} ({self.project})"


class AliyunEIP(models.Model):
    allocation_id = models.CharField('EIP ID', max_length=128, primary_key=True)
    name = models.CharField('名称', max_length=128, blank=True, null=True)
    account_name = models.CharField('所属账号', max_length=64)
    region_id = models.CharField('地域ID', max_length=32)
    status = models.CharField('状态', max_length=32)
    instance_id = models.CharField('绑定的实例ID', max_length=128, blank=True, null=True)
    instance_type = models.CharField('绑定的实例类型', max_length=64, blank=True, null=True)
    bandwidth = models.CharField('带宽峰值', max_length=32)
    internet_charge_type = models.CharField('计费方式', max_length=32)
    ip_address = models.CharField('IP地址', max_length=64)
    allocation_time = models.DateTimeField('创建时间', default=timezone.now)
    expired_time = models.DateTimeField('过期时间', blank=True, null=True, default=None)
    tags = models.JSONField('标签', default=dict)
    monthly_flow = models.FloatField('当月流量(GB)', default=0)
    monthly_requests = models.IntegerField('当月请求数', default=0)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '阿里云弹性公网IP'
        verbose_name_plural = '阿里云弹性公网IP'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.ip_address})" if self.name else self.ip_address

class AliyunWAF(models.Model):
    # 核心标识信息
    instance_id = models.CharField('实例ID', max_length=128, primary_key=True)
    region_id = models.CharField('地域', max_length=64, default='cn-hangzhou')
    account_name = models.CharField('所属账号', max_length=128)

    # 状态与版本信息
    status = models.IntegerField('状态', default=1, choices=[
        (1, '正常'),
        (2, '到期'),
        (3, '释放')
    ])
    pay_type = models.CharField('付费类型', max_length=32, default='PREPAY', choices=[
        ('PREPAY', '包年包月'),
        ('POSTPAY', '按量付费')
    ])
    edition = models.CharField('WAF版本', max_length=64, blank=True, null=True)

    # 时间信息
    start_time = models.DateTimeField('开始时间', default=timezone.now)
    end_time = models.DateTimeField('到期时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    # 能力支持标志
    tamperproof = models.BooleanField('网页防篡改支持', default=False)
    bot = models.BooleanField('Bot管理支持', default=False)
    custom_rule = models.BooleanField('自定义规则支持', default=False)
    ip_blacklist = models.BooleanField('IP黑名单支持', default=False)
    dlp = models.BooleanField('信息泄露防护支持', default=False)
    anti_scan = models.BooleanField('扫描防护支持', default=False)
    log_service = models.BooleanField('日志服务支持', default=False)

    # 规格详情
    details = JSONField('详细配置', default=dict)
    all_details = JSONField('全部配置', default=dict)

    class Meta:
        verbose_name = '阿里云WAF实例'
        verbose_name_plural = '阿里云WAF实例'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['pay_type']),
            models.Index(fields=['region_id']),
        ]

    def __str__(self):
        return f"{self.instance_name or self.instance_id} ({self.get_status_display()})"

    @property
    def capability_list(self):
        """返回支持的能力列表"""
        capabilities = []
        if self.tamperproof:
            capabilities.append('网页防篡改')
        if self.bot:
            capabilities.append('Bot管理')
        if self.custom_rule:
            capabilities.append('自定义规则')
        if self.ip_blacklist:
            capabilities.append('IP黑名单')
        if self.dlp:
            capabilities.append('信息泄露防护')
        if self.anti_scan:
            capabilities.append('扫描防护')
        if self.log_service:
            capabilities.append('日志服务')
        return capabilities

    @property
    def pay_type_display(self):
        return dict(self._meta.get_field('pay_type').choices).get(self.pay_type, self.pay_type)

    @property
    def status_display(self):
        return dict(self._meta.get_field('status').choices).get(self.status, self.status)

class AliyunNAS(models.Model):
    STORAGE_TYPE_CHOICES = [
        ('Capacity', '容量型'),
        ('Performance', '性能型'),
        ('standard', '标准型'),
        ('advance', '高级型'),
    ]

    PROTOCOL_TYPE_CHOICES = [
        ('NFS', 'NFS'),
        ('SMB', 'SMB'),
        ('cpfs', 'CPFS'),
    ]

    STATUS_CHOICES = [
        ('Pending', '创建中'),
        ('Running', '运行中'),
        ('Stopped', '已停止'),
        ('Deleting', '删除中'),
    ]

    file_system_id = models.CharField('文件系统ID', max_length=128, primary_key=True)
    file_system_name = models.CharField('文件系统名称', max_length=128)
    account_name = models.CharField('所属账号', max_length=64)
    region_id = models.CharField('地域ID', max_length=32)
    description = models.TextField('描述', blank=True, null=True)
    protocol_type = models.CharField('协议类型', max_length=20, choices=PROTOCOL_TYPE_CHOICES)
    storage_type = models.CharField('存储类型', max_length=20, choices=STORAGE_TYPE_CHOICES)
    metered_size = models.BigIntegerField('计量容量(GB)', default=0)
    capacity = models.BigIntegerField('实际容量(GB)', default=0)
    bandwidth = models.IntegerField('带宽(MB/s)', default=0)
    zone_id = models.CharField('可用区', max_length=64)
    vpc_id = models.CharField('VPC ID', max_length=128)
    vswitch_id = models.CharField('交换机ID', max_length=128)
    create_time = models.DateTimeField(null=True, blank=True, default=None)
    mount_target_count = models.IntegerField('挂载点数量', default=0)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES)
    pay_type = models.CharField('付费类型', max_length=20, default='PayAsYouGo')
    tags = models.JSONField('标签', default=dict)
    monthly_flow = models.FloatField('当月流量(GB)', default=0)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    # 项目归属信息（从 ProjectAliyunNAS 同步）
    project = models.CharField('所属项目', max_length=255, null=True, blank=True)
    environment = models.CharField('环境类型', max_length=50, null=True, blank=True)
    owner = models.CharField('负责人', max_length=100, null=True, blank=True)
    remark = models.TextField('说明', null=True, blank=True)

    class Meta:
        verbose_name = '阿里云文件存储NAS'
        verbose_name_plural = '阿里云文件存储NAS'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.file_system_name} ({self.file_system_id})"


class ProjectAliyunNAS(models.Model):
    """阿里云NAS项目元数据管理"""
    lookup_field = 'id'
    file_system_name = models.CharField(
        "文件系统名称",
        max_length=255,
        unique=True,
        help_text="唯一标识NAS文件系统的名称"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="NAS文件系统所属的项目名称"
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
        help_text="NAS文件系统所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="NAS文件系统的主要负责人"
    )
    description = models.TextField(
        "说明",
        blank=True,
        null=True,
        help_text="NAS文件系统的详细说明"
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
        verbose_name = "阿里云NAS项目元数据"
        verbose_name_plural = "阿里云NAS项目元数据"
        ordering = ['project', 'file_system_name']
        indexes = [
            models.Index(fields=['file_system_name']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return f"{self.file_system_name} ({self.project})"


class ProjectAliyunSLS(models.Model):
    """阿里云SLS项目元数据管理"""
    lookup_field = 'id'
    project_name = models.CharField(
        "Project名称",
        max_length=128,
        unique=True,
        help_text="唯一标识SLS Project的名称"
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        help_text="SLS Project所属的项目名称"
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
        help_text="SLS Project所在的环境分类"
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        help_text="SLS Project的主要负责人"
    )
    department = models.CharField(
        "所属部门",
        max_length=100,
        blank=True,
        null=True,
        help_text="SLS Project所属的部门"
    )
    business_unit = models.CharField(
        "业务单元",
        max_length=100,
        blank=True,
        null=True,
        help_text="SLS Project所属的业务单元"
    )
    description = models.TextField(
        "说明",
        blank=True,
        null=True,
        help_text="SLS Project的详细说明"
    )
    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True
    )
    notes = models.TextField(
        "备注",
        blank=True,
        null=True,
        help_text="附加说明信息"
    )

    class Meta:
        verbose_name = "阿里云SLS项目元数据"
        verbose_name_plural = "阿里云SLS项目元数据"
        ordering = ['project', 'project_name']

    def __str__(self):
        return f"{self.project_name} ({self.project})"



class AliyunSNATEntry(models.Model):

    snat_entry_id = models.CharField("SNAT条目ID", max_length=128, primary_key=True)
    snat_table_id = models.CharField("SNAT表ID", max_length=128)
    nat_gateway_id = models.CharField("NAT网关ID", max_length=128, db_index=True)  # 直接加索引
    snat_entry_name = models.CharField("SNAT条目名称", max_length=128, blank=True)
    source_cidr = models.CharField("源网段", max_length=64, db_index=True)
    snat_ip = models.GenericIPAddressField("公网IP", db_index=True)
    source_vswitch_id = models.CharField("源交换机ID", max_length=128, blank=True)
    network_interface_id = models.CharField("弹性网卡ID", max_length=128, blank=True)
    status = models.CharField("状态", max_length=32, default='Available')
    region_id = models.CharField("地域ID", max_length=32)
    account_name = models.CharField("所属账号", max_length=100)
    eip_affinity = models.CharField("IP亲和性", max_length=10, blank=True)
    tags = models.JSONField("标签", default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hostname = models.CharField(
        "匹配的主机名",
        max_length=500,
        blank=True,
        null=True,
        db_index=True,
        help_text="根据源网段匹配到的ECS主机名（多个用逗号分隔）"
    )

    class Meta:
        verbose_name = "阿里云SNAT条目"
        verbose_name_plural = "阿里云SNAT条目"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['snat_table_id']),
            models.Index(fields=['region_id']),
            models.Index(fields=['source_cidr']),
            models.Index(fields=['hostname']),
            models.Index(fields=['snat_ip']),
            # nat_gateway_id 已通过 db_index=True 添加，无需重复
        ]

    def __str__(self):
        return f"{self.snat_entry_name or '未命名'} ({self.snat_entry_id})"

class AliyunSLSProject(models.Model):
    project_name = models.CharField(max_length=255, unique=True, verbose_name="Project名称")
    account_name = models.CharField(max_length=100, verbose_name="所属账号")
    region_id = models.CharField(max_length=50, verbose_name="地域ID")
    description = models.TextField(blank=True, verbose_name="描述")
    status = models.CharField(max_length=50, default='Running', verbose_name="状态")
    create_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    last_modify_time = models.DateTimeField(null=True, blank=True, verbose_name="最后修改时间")
    data_redundancy_type = models.CharField(
        max_length=20,
        null=True,
        default='LRS',
        verbose_name='数据冗余类型',
        help_text='LRS (本地冗余存储) 或 ZRS (同城冗余存储)'
    )
    recycle_bin_enabled = models.BooleanField(
        null=True,  # ⚠️ 关键：数据库允许NULL
        blank=True,  # Django Admin/表单允许为空
        verbose_name='回收站是否开启'
    )
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name="同步时间")

    class Meta:
        db_table = 'aliyun_sls_project'
        verbose_name = 'SLS Project'
        verbose_name_plural = 'SLS Projects'
        ordering = ['-updated_at']

    # 新增字段
    project = models.CharField('所属项目', max_length=255, null=True, blank=True)
    environment = models.CharField('环境类型', max_length=50, null=True, blank=True)
    owner = models.CharField('负责人', max_length=100, null=True, blank=True)
    remark = models.TextField('说明', null=True, blank=True)

    def __str__(self):
        return f"{self.account_name} - {self.project_name}"


class AliyunSLSLogStore(models.Model):
    project = models.ForeignKey(AliyunSLSProject, on_delete=models.CASCADE, related_name='logstores', verbose_name="所属Project")
    logstore_name = models.CharField(max_length=255, verbose_name="LogStore名称")
    ttl = models.IntegerField(default=90, verbose_name="TTL(天)")
    shard_count = models.IntegerField(default=2, verbose_name="分片数")
    enable_tracking = models.BooleanField(default=False, verbose_name="启用追踪")
    auto_split = models.BooleanField(default=False, verbose_name="自动分裂Shard")
    max_split_shard = models.IntegerField(default=0, verbose_name="最大分裂Shard数")
    append_meta = models.BooleanField(default=False, verbose_name="记录外网IP")
    telemetry_type = models.CharField(max_length=20, default='None', verbose_name="日志类型")
    create_time = models.DateTimeField(null=True, blank=True, verbose_name="创建时间")
    last_modify_time = models.DateTimeField(null=True, blank=True, verbose_name="最后修改时间")
    encrypt_conf = models.JSONField(null=True, blank=True, verbose_name="加密配置")
    hot_ttl = models.IntegerField(null=True, blank=True, verbose_name="热存储层TTL")
    infrequent_access_ttl = models.IntegerField(null=True, blank=True, verbose_name="低频存储TTL")
    mode = models.CharField(max_length=20, default='standard', verbose_name="Logstore类型")
    product_type = models.CharField(max_length=50, default='', verbose_name="产品类型")
    processor_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="IngestProcessor ID")
    # sharding_policy, shard_group, shard_hash 等复杂字段可以用 JSONField 存储
    sharding_policy = models.JSONField(null=True, blank=True, verbose_name="分片策略")
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name="同步时间")
    account_name = models.CharField(max_length=100, verbose_name='所属账号', blank=True)

    def save(self, *args, **kwargs):
        # 在保存前，自动从关联的 project 同步 account_name
        if self.project and self.project.account_name:
            self.account_name = self.project.account_name
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'aliyun_sls_logstore'
        verbose_name = 'SLS LogStore'
        verbose_name_plural = 'SLS LogStores'
        unique_together = ('project', 'logstore_name')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.project.project_name} - {self.logstore_name}"


# models.py（部分调整）
from django.db import models
import pytz
from datetime import datetime, timezone
from django.utils import timezone as django_timezone


class AliyunSecurityGroup(models.Model):
    security_group_id = models.CharField("安全组ID", max_length=255, primary_key=True)
    security_group_name = models.CharField("安全组名称", max_length=255)
    description = models.CharField("描述", max_length=255, null=True, blank=True)
    vpc_id = models.CharField("VPC ID", max_length=255, null=True, blank=True)
    region_id = models.CharField("地域ID", max_length=50)
    account_name = models.CharField("所属账号", max_length=100)
    creation_time = models.DateTimeField("创建时间", null=True, blank=True)  # 改为 DateTimeField
    value = models.CharField("标签值", max_length=255, null=True, blank=True)
    ecs_count = models.IntegerField("关联ECS数量", default=0)
    rule_count = models.IntegerField("规则数量", default=0)
    tags = models.JSONField("标签", default=dict, blank=True)  # 新增标签字段

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "阿里云安全组"
        verbose_name_plural = "阿里云安全组"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['security_group_id']),
            models.Index(fields=['security_group_name']),
            models.Index(fields=['vpc_id']),
            models.Index(fields=['region_id', 'account_name']),
        ]

    def __str__(self):
        return f"{self.security_group_name} ({self.security_group_id})"


# 协议选择保持不变
SECURITY_GROUP_PROTOCOL_CHOICES = (
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
    ('all', 'ALL'),
    ('gre', 'GRE'),
    ('icmpv6', 'ICMPv6'),
)


class AliyunSecurityGroupRule(models.Model):
    rule_id = models.CharField("规则ID", max_length=255, primary_key=True)
    security_group = models.ForeignKey(
        AliyunSecurityGroup,
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name="所属安全组"
    )
    direction = models.CharField("方向", max_length=10, choices=(('ingress', '入方向'), ('egress', '出方向')))
    ip_protocol = models.CharField("协议", max_length=10, choices=SECURITY_GROUP_PROTOCOL_CHOICES)
    port_range = models.CharField("端口范围", max_length=50)
    source_cidr_ip = models.CharField("源IP地址段", max_length=255, null=True, blank=True)
    dest_cidr_ip = models.CharField("目标IP地址段", max_length=255, null=True, blank=True)
    policy = models.CharField("策略", max_length=10)  # accept, drop
    priority = models.IntegerField("优先级")
    description = models.CharField("描述", max_length=255, null=True, blank=True)
    creation_time = models.DateTimeField("创建时间", null=True, blank=True)  # 改为 DateTimeField
    source_group_id = models.CharField("源安全组ID", max_length=255, null=True, blank=True)
    source_group_owner_account = models.CharField("源安全组所属账号", max_length=100, null=True, blank=True)
    dest_group_id = models.CharField("目标安全组ID", max_length=255, null=True, blank=True)
    dest_group_owner_account = models.CharField("目标安全组所属账号", max_length=100, null=True, blank=True)
    ipv6_source_cidr_ip = models.CharField("IPv6源地址段", max_length=255, null=True, blank=True)
    ipv6_dest_cidr_ip = models.CharField("IPv6目标地址段", max_length=255, null=True, blank=True)
    source_prefix_list_id = models.CharField("源前缀列表ID", max_length=255, null=True, blank=True)
    dest_prefix_list_id = models.CharField("目标前缀列表ID", max_length=255, null=True, blank=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "阿里云安全组规则"
        verbose_name_plural = "阿里云安全组规则"
        ordering = ['security_group', 'direction', 'priority']
        indexes = [
            models.Index(fields=['rule_id']),
            models.Index(fields=['direction']),
            models.Index(fields=['ip_protocol']),
            models.Index(fields=['source_cidr_ip']),
            models.Index(fields=['dest_cidr_ip']),
            models.Index(fields=['security_group', 'direction']),
        ]

    def __str__(self):
        return f"{self.direction} {self.ip_protocol}:{self.port_range}"
