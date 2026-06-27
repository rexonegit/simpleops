# apps/rbac/views/role.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.utils.response import ApiResponse
from apps.rbac.models import Role, Permission, Router
from django.db import transaction
from django.forms.models import model_to_dict


class RoleListView(APIView):
    """角色列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = Role.objects.all().order_by('id')
        data = []
        for r in roles:
            data.append({
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "description": r.description or "",
                "menu_count": r.menus.count(),
                "permission_count": r.permissions.count(),
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(r, 'created_at') else ""
            })
        return ApiResponse.success({
            "list": data,
            "total": len(data)
        })


class RoleCreateView(APIView):
    """新增角色"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")
        code = request.data.get("code")
        description = request.data.get("description", "")

        if not name or not code:
            return ApiResponse.error("角色名称和编码不能为空")

        if Role.objects.filter(code=code).exists():
            return ApiResponse.error("角色编码已存在")

        role = Role.objects.create(
            name=name,
            code=code,
            description=description
        )
        return ApiResponse.success({
            "msg": "创建成功",
            "id": role.id
        })


class RoleUpdateView(APIView):
    """编辑角色"""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return ApiResponse.error("角色不存在")

        if role.code == "admin":
            return ApiResponse.error("禁止修改超级管理员角色")

        name = request.data.get("name", role.name)
        code = request.data.get("code", role.code)
        description = request.data.get("description", role.description)

        if Role.objects.filter(code=code).exclude(pk=pk).exists():
            return ApiResponse.error("角色编码已存在")

        role.name = name
        role.code = code
        role.description = description
        role.save()

        return ApiResponse.success("更新成功")


class RoleDeleteView(APIView):
    """删除角色"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return ApiResponse.error("角色不存在")

        if role.code == "admin":
            return ApiResponse.error("禁止删除超级管理员角色")

        if role.user_set.exists():
            return ApiResponse.error("该角色正在被用户使用，无法删除")

        role.delete()
        return ApiResponse.success("删除成功")


class RolePermissionsView(APIView):
    """获取角色已分配的权限（菜单 + 按钮）"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return ApiResponse.error("角色不存在")

        # 构建菜单树（只包含目录和菜单）
        def build_menu_tree(qs, parent=None):
            tree = []
            for m in qs.filter(parent=parent, type__in=[0, 1]).order_by('sort'):
                node = {
                    "id": m.id,
                    "label": m.title,
                    "children": build_menu_tree(qs, m)
                }
                tree.append(node)
            return tree

        menu_tree = build_menu_tree(Router.objects.all())

        # 获取按钮权限（type=2）
        button_perms = []
        for router in Router.objects.filter(type=2):
            for perm in router.permissions.all():
                button_perms.append({
                    "id": f"perm_{perm.id}",
                    "label": f"{router.title} - {perm.name}",
                    "parentId": router.parent.id if router.parent else None
                })

        # 已分配的权限
        checked_menu_ids = list(role.menus.filter(type__in=[0, 1]).values_list('id', flat=True))
        checked_perm_ids = [f"perm_{p.id}" for p in role.permissions.all()]

        return ApiResponse.success({
            "menuTree": menu_tree,
            "buttonPerms": button_perms,
            "checkedMenuIds": checked_menu_ids,
            "checkedPermIds": checked_perm_ids
        })


class AssignPermissionsView(APIView):
    """给角色分配权限（菜单 + 按钮）"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        role_id = request.data.get("roleId")
        menu_ids = request.data.get("menuIds", [])  # 菜单和目录
        perm_ids = request.data.get("permIds", [])  # 按钮权限ID，格式: perm_123

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return ApiResponse.error("角色不存在")

        if role.code == "admin":
            return ApiResponse.error("禁止修改超级管理员权限")

        # 处理菜单权限
        role.menus.set(menu_ids)

        # 处理按钮权限
        real_perm_ids = []
        for item in perm_ids:
            if str(item).startswith("perm_"):
                real_perm_ids.append(int(item.replace("perm_", "")))
        permissions = Permission.objects.filter(id__in=real_perm_ids)
        role.permissions.set(permissions)

        return ApiResponse.success("权限分配成功")