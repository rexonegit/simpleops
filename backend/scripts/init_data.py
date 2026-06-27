#!/usr/bin/env python
# scripts/init_data.py
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_vue_admin.settings')
django.setup()

from apps.users.models import User
from apps.rbac.models import Router, Permission, Role


def run():
    print("开始初始化数据库（最新规范版）...")

    Router.objects.all().delete()
    Permission.objects.all().delete()
    Role.objects.all().delete()

    # 首页（关键：component 写完整路径或短路径均可）
    Router.objects.create(
        title="首页",
        name="Index",
        path="/",
        component="/index/index",    # → 前端收到 @/views/index/index
        redirect="index",
        icon="home",
        type=1,
        affix=True,
        keep_alive=True,
        sort=0
    )

    # 权限管理
    perm_dir = Router.objects.create(
        title="权限管理",
        name="Permission",
        path="/permission",
        component="Layout",
        icon="lock",
        type=0,
        always_show=True,
        sort=10,
        redirect="user"   # 重定向到第一个子菜单（name）
    )
    Router.objects.create(parent=perm_dir, title="用户管理", name="UserList", path="user", component="permission/user", type=1, sort=1)
    Router.objects.create(parent=perm_dir, title="角色管理", name="RoleList", path="role", component="permission/role", type=1, sort=2)
    Router.objects.create(parent=perm_dir, title="菜单管理", name="MenuList", path="menu", component="permission/menu", type=1, sort=3)

    # 系统监控
    monitor = Router.objects.create(
        title="系统监控",
        name="Monitor",
        path="/monitor",
        component="Layout",
        icon="monitor",
        type=0,
        sort=20
    )
    logs = Router.objects.create(parent=monitor, title="日志审计", name="Logs", path="logs", component="Layout", type=0)
    Router.objects.create(parent=logs, title="操作日志", name="OperationLog", path="operation", component="logs/operation", type=1)
    Router.objects.create(parent=logs, title="登录日志", name="LoginLog", path="login", component="logs/login", type=1)

    # 按钮权限
    perms = [
        ("user:list", "查看用户"), ("user:add", "新增用户"),
        ("role:list", "查看角色"), ("menu:list", "查看菜单"),
    ]
    for code, name in perms:
        Permission.objects.get_or_create(code=code, defaults={"name": name})

    # 超级管理员
    role, _ = Role.objects.get_or_create(name="超级管理员", code="admin")
    role.menus.set(Router.objects.filter(type__in=[0, 1, 3]))
    role.permissions.set(Permission.objects.all())

    admin, _ = User.objects.get_or_create(username="admin", defaults={"is_superuser": True, "is_staff": True})
    admin.set_password("123456")
    admin.save()
    admin.roles.add(role)

    print("初始化完成！component 原始输出 + redirect 使用 name 方式")


if __name__ == "__main__":
    run()