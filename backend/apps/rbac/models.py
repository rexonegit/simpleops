# apps/rbac/models.py
from django.db import models


class Router(models.Model):
    """
    菜单&路由表（完全对齐 vue-router + vab 官方格式）
    """
    TYPE_CHOICES = (
        (0, '目录'),  # Layout / EmptyLayout
        (1, '菜单'),  # 真实页面
        (2, '按钮/权限'),  # 纯权限标识，不生成路由
        (3, '外链'),  # path = http(s)://
    )

    title = models.CharField(max_length=50, verbose_name="菜单标题")
    name = models.CharField(max_length=64, unique=True, verbose_name="路由name（全局唯一）")
    path = models.CharField(max_length=255, verbose_name="路由path或外链URL")

    # component 规则：
    # type=0（目录） → "Layout" 或 "EmptyLayout"（后端自动判断）
    # type=1（菜单） → "@/views/xxx/xxx"（前端约定格式）
    # type=3（外链） → "external"
    component = models.CharField(max_length=255, blank=True, null=True, verbose_name="组件路径")

    redirect = models.CharField(max_length=255, blank=True, null=True, verbose_name="重定向")
    icon = models.CharField(max_length=100, blank=True, null=True, verbose_name="图标")

    # === vab 核心字段 ===
    hidden = models.BooleanField(default=False, verbose_name="是否隐藏")
    always_show = models.BooleanField(default=False, verbose_name="强制显示（只有一个子菜单时）")
    keep_alive = models.BooleanField(default=False, verbose_name="是否缓存（keepAlive）")
    affix = models.BooleanField(default=False, verbose_name="固定在tagsView")
    badge = models.CharField(max_length=50, blank=True, null=True, verbose_name="角标")

    sort = models.IntegerField(default=0, verbose_name="排序")
    type = models.SmallIntegerField(choices=TYPE_CHOICES, default=1, verbose_name="类型")
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name="父级"
    )

    class Meta:
        ordering = ['sort', 'id']
        verbose_name = "路由菜单"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Permission(models.Model):
    """
    按钮权限（彻底与 Router 解耦！）
    """
    code = models.CharField(max_length=100, unique=True, verbose_name="权限标识")
    name = models.CharField(max_length=100, verbose_name="权限名称")
    # 可选绑定到某个菜单（用于后台管理时显示归属），但不影响权限判断
    router = models.ForeignKey(
        Router,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='permissions',
        verbose_name="关联菜单（可选）"
    )

    class Meta:
        verbose_name = "按钮权限"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="角色名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="角色编码")
    description = models.TextField(blank=True, null=True, verbose_name="描述")

    # 菜单权限（控制左侧菜单显示）
    menus = models.ManyToManyField(
        Router,
        limit_choices_to={'type__in': [0, 1, 3]},  # 只选目录、菜单、外链
        blank=True,
        verbose_name="菜单权限"
    )
    # 按钮权限（控制页面内按钮显示）
    permissions = models.ManyToManyField(Permission, blank=True, verbose_name="按钮权限")

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name