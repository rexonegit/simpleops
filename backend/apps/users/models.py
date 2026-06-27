from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name="手机号")
    avatar = models.ImageField(upload_to='avatar/', blank=True, null=True, verbose_name="头像")
    roles = models.ManyToManyField('rbac.Role', blank=True, verbose_name="角色")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username