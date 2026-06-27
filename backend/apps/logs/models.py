from django.db import models
from apps.users.models import User


class LoginLog(models.Model):
    username = models.CharField(max_length=50, verbose_name="用户名")
    ip = models.CharField(max_length=45, verbose_name="IP地址")
    user_agent = models.CharField(max_length=500, blank=True, verbose_name="User-Agent")
    status = models.BooleanField(default=True, verbose_name="是否成功")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登录时间")

    class Meta:
        verbose_name = "登录日志"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


class OperationLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name="操作人")
    ip = models.CharField(max_length=45, verbose_name="IP地址")
    method = models.CharField(max_length=10, verbose_name="请求方法")
    path = models.CharField(max_length=500, verbose_name="请求路径")
    action = models.CharField(max_length=100, verbose_name="操作类型")
    status_code = models.IntegerField(verbose_name="状态码")
    duration = models.IntegerField(verbose_name="耗时(ms)")
    request_body = models.TextField(blank=True, verbose_name="请求数据")
    response_body = models.TextField(blank=True, verbose_name="响应数据")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']