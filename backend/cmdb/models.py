from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

class NetworkSegment(models.Model):
    """网段/子网模型"""
    TYPE_CHOICES = (
        ('intranet', '内网'),
        ('internet', '外网/公网'),
    )
    
    name = models.CharField("网段名称", max_length=100)
    segment = models.CharField("网段CIDR", max_length=50, unique=True, help_text="例如: 192.168.1.0/24")
    mask = models.CharField("子网掩码", max_length=50, blank=True, null=True)
    gateway = models.GenericIPAddressField("网关地址", blank=True, null=True)
    vlan_id = models.IntegerField("VLAN ID", blank=True, null=True)
    type = models.CharField("类型", max_length=20, choices=TYPE_CHOICES, default='intranet')
    location = models.CharField("位置/区域", max_length=100, blank=True, null=True, help_text="机房或地域")
    description = models.TextField("备注", blank=True, null=True)
    
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "网段管理"
        verbose_name_plural = "网段管理"
        ordering = ['segment']

    def __str__(self):
        return f"{self.name} ({self.segment})"


class IPAddress(models.Model):
    """IP地址模型"""
    STATUS_CHOICES = (
        ('used', '使用中'),
        ('available', '空闲'),
        ('reserved', '保留'),
        ('deprecated', '废弃'),
    )
    
    SOURCE_CHOICES = (
        ('manual', '手动录入'),
        ('aliyun', '阿里云同步'),
        ('datacenter', '本地机房同步'),
    )

    TYPE_CHOICES = (
        ('intranet', '内网'),
        ('internet', '外网/公网'),
    )
    
    # 核心字段
    ip_address = models.GenericIPAddressField("IP地址", unique=True, db_index=True)
    type = models.CharField("地址类型", max_length=20, choices=TYPE_CHOICES, default='intranet', db_index=True)
    network_segment = models.ForeignKey(NetworkSegment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="所属网段", related_name='ips')
    
    # 基础信息
    hostname = models.CharField("主机名", max_length=255, blank=True, null=True)
    mac_address = models.CharField("MAC地址", max_length=100, blank=True, null=True)
    mask = models.CharField("掩码", max_length=50, blank=True, null=True)
    
    # 管理信息
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default='used')
    source = models.CharField("来源", max_length=20, choices=SOURCE_CHOICES, default='manual')
    environment = models.CharField("环境类型", max_length=50, blank=True, null=True)
    owner = models.CharField("负责人", max_length=100, blank=True, null=True)
    location = models.CharField("位置", max_length=100, blank=True, null=True)
    is_gateway = models.BooleanField("是否网关", default=False)
    description = models.TextField("备注", blank=True, null=True)
    
    # 关联资源（通过ContentType关联不同模型的实例）
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    bound_resource = GenericForeignKey('content_type', 'object_id')
    
    # 辅助字段
    bound_instance_name = models.CharField("绑定实例名称", max_length=255, blank=True, null=True, help_text="冗余字段，便于显示")

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "IP地址管理"
        verbose_name_plural = "IP地址管理"
        ordering = ['ip_address']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return self.ip_address



class cmdbdatabase(models.Model):
    """数据库实例元数据管理"""
    DB_TYPE_CHOICES = (
        ('oracle', 'Oracle'),
        ('mysql', 'MySQL'),
        ('mongodb', 'MongoDB'),
        ('postgresql', 'PostgreSQL'),
        ('sqlserver', 'SQL Server'),
        ('redis', 'Redis'),
        ('elasticsearch', 'Elasticsearch'),
        ('other', 'Other'),
    )

    ENVIRONMENT_CHOICES = (
        ('prod', '生产环境'),
        ('test', '测试环境'),
        ('dev', '开发环境'),
        ('uat', '用户验收环境'),
        ('stg', '预生产环境'),
        ('dr', '灾备环境'),
        ('other', '其他'),
    )

    name = models.CharField(
        "数据库名称",
        max_length=255,
        unique=True,
        help_text="唯一标识数据库实例的名称"
    )
    db_type = models.CharField(
        "数据库类型",
        max_length=50,
        choices=DB_TYPE_CHOICES,
        default='mysql'
    )
    version = models.CharField(
        "数据库版本",
        max_length=100,
        blank=True,
        null=True
    )
    project = models.CharField(
        "所属项目",
        max_length=255,
        null=True,
        blank=True,
        help_text="数据库所属的项目名称"
    )
    environment = models.CharField(
        "环境类型",
        max_length=50,
        choices=ENVIRONMENT_CHOICES,
        default='prod'
    )
    owner = models.CharField(
        "负责人",
        max_length=100,
        null=True,
        blank=True
    )
    host = models.CharField(
        "主机地址",
        max_length=100,
        help_text="数据库所在服务器IP或主机名"
    )
    port = models.IntegerField(
        "端口号",
        default=0
    )
    instance = models.CharField(
        "实例名/SID",
        max_length=100,
        blank=True,
        null=True
    )
    db_name = models.CharField(
        "数据库名",
        max_length=100,
        blank=True,
        null=True
    )
    charset = models.CharField(
        "字符集",
        max_length=50,
        blank=True,
        null=True
    )
    cpu = models.CharField(
        "CPU分配",
        max_length=50,
        blank=True,
        null=True,
        help_text="如: 4核"
    )
    memory = models.CharField(
        "内存分配",
        max_length=50,
        blank=True,
        null=True,
        help_text="如: 16GB"
    )
    disk = models.CharField(
        "磁盘大小",
        max_length=50,
        blank=True,
        null=True,
        help_text="如: 500GB"
    )
    connection_string = models.TextField(
        "连接字符串",
        blank=True,
        null=True
    )
    username = models.CharField(
        "用户名",
        max_length=100,
        blank=True,
        null=True
    )
    password = models.CharField(
        "密码",
        max_length=255,
        blank=True,
        null=True
    )
    backup_policy = models.TextField(
        "备份策略",
        blank=True,
        null=True
    )
    maintenance_window = models.CharField(
        "维护窗口",
        max_length=100,
        blank=True,
        null=True,
        help_text="如: 每周六 03:00-05:00"
    )
    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True
    )
    description = models.TextField(
        "备注",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "数据库实例元数据"
        verbose_name_plural = "数据库实例元数据"
        ordering = ['project', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['project']),
            models.Index(fields=['environment']),
            models.Index(fields=['owner']),
            models.Index(fields=['db_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.db_type})"