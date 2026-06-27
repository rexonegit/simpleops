from django.db import models
from django.utils import timezone


class AlertRecord(models.Model):
    """告警记录管理"""
    
    class AlertLevel(models.TextChoices):
        WARNING = 'warning', '警告'
        CRITICAL = 'critical', '严重'
        FATAL = 'fatal', '致命'
    
    class CurrentStatus(models.TextChoices):
        PROBLEM = 'PROBLEM', '告警中'
        RECOVERY = 'RECOVERY', '已恢复'
        MUTED = 'MUTED', '已屏蔽'
    
    class HandleType(models.TextChoices):
        MUTE = 'mute', '屏蔽'
        SUPPRESS = 'suppress', '抑制通知'
        DOWNGRADE = 'downgrade', '降级'
        OTHER = 'other', '其他'
    
    # 告警信息（原始内容）
    alert_info = models.TextField(
        '告警信息',
        blank=True,
        null=True,
        help_text='完整告警描述（直接复制原始告警内容）'
    )
    
    # 登记信息
    registered_at = models.DateTimeField(
        '登记时间',
        auto_now_add=True,
        help_text='系统自动获取'
    )
    registered_by = models.CharField(
        '登记人',
        max_length=100,
        blank=True,
        null=True,
        help_text='从系统自动获取为当前登陆用户'
    )
    
    # 告警基本信息
    alert_name = models.CharField(
        '告警名称',
        max_length=255,
        help_text='简短描述告警内容'
    )
    project = models.CharField(
        '项目',
        max_length=255,
        help_text='OA、OracleDB-host、帆软BI 等'
    )
    host = models.CharField(
        '告警主机',
        max_length=255,
        help_text='主机名称'
    )
    ip_address = models.CharField(
        'IP地址',
        max_length=50,
        help_text='主机IP'
    )
    
    # 告警类型和监控项
    alert_type = models.CharField(
        '告警类型',
        max_length=100,
        blank=True,
        null=True,
        help_text='exporter类型或监控来源'
    )
    monitor_item = models.CharField(
        '监控项',
        max_length=255,
        blank=True,
        null=True,
        help_text='具体监控指标'
    )
    
    # 阈值和触发值
    threshold = models.CharField(
        '阈值',
        max_length=50,
        help_text='告警阈值'
    )
    trigger_value = models.CharField(
        '触发时值',
        max_length=50,
        help_text='触发时的实际值'
    )
    
    # 告警级别和状态
    alert_level = models.CharField(
        '告警级别',
        max_length=20,
        choices=AlertLevel.choices,
        default=AlertLevel.WARNING
    )
    trigger_time = models.DateTimeField(
        '触发时间',
        help_text='告警首次触发时间'
    )
    recovery_time = models.DateTimeField(
        '恢复时间',
        blank=True,
        null=True,
        help_text='如果已恢复，填写恢复时间'
    )
    duration = models.CharField(
        '持续时长',
        max_length=50,
        blank=True,
        null=True,
        help_text='当前或最终持续时长，可自动计算'
    )
    current_status = models.CharField(
        '当前状态',
        max_length=20,
        choices=CurrentStatus.choices,
        default=CurrentStatus.PROBLEM
    )
    
    # 特殊处理信息
    special_handle_type = models.CharField(
        '特殊处理类型',
        max_length=20,
        choices=HandleType.choices,
        default=HandleType.MUTE
    )
    mute_reason = models.TextField(
        '屏蔽/处理原因',
        help_text='人工输入'
    )
    mute_end_time = models.DateTimeField(
        '屏蔽结束时间',
        blank=True,
        null=True,
        help_text='预计或实际结束时间'
    )
    is_permanent_mute = models.BooleanField(
        '是否永久屏蔽',
        default=False
    )
    
    # 备注
    remarks = models.TextField(
        '备注',
        blank=True,
        null=True,
        help_text='其他补充说明'
    )
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '告警记录'
        verbose_name_plural = '告警记录'
        ordering = ['-registered_at']
        indexes = [
            models.Index(fields=['alert_name']),
            models.Index(fields=['project']),
            models.Index(fields=['host']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['alert_level']),
            models.Index(fields=['current_status']),
            models.Index(fields=['trigger_time']),
            models.Index(fields=['registered_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_name} - {self.host} ({self.get_current_status_display()})"
    
    def save(self, *args, **kwargs):
        # 自动计算持续时长
        if self.trigger_time:
            end_time = self.recovery_time or timezone.now()
            delta = end_time - self.trigger_time
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days > 0:
                self.duration = f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                self.duration = f"{hours}h {minutes}m {seconds}s"
            else:
                self.duration = f"{minutes}m {seconds}s"
        super().save(*args, **kwargs)
