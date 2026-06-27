# apps/rbac/views/menu.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.utils.response import ApiResponse
from apps.rbac.models import Router, Permission
from django.forms.models import model_to_dict
from django.db import transaction


class MenuTreeView(APIView):
    """获取菜单树（用于菜单管理页面展示）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        def build_tree(queryset, parent=None):
            tree = []
            for item in queryset.filter(parent=parent).order_by('sort', 'id'):
                node = model_to_dict(item)
                node["id"] = item.id
                node["label"] = item.title
                node["children"] = build_tree(queryset, item)
                tree.append(node)
            return tree

        tree = build_tree(Router.objects.all())
        return ApiResponse.success(tree)


class MenuCreateView(APIView):
    """新增菜单"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data
        parent_id = data.get("parent")
        parent = Router.objects.get(id=parent_id) if parent_id and parent_id != "null" else None

        router = Router.objects.create(
            parent=parent,
            title=data["title"],
            name=data["name"],
            path=data["path"],
            component=data.get("component") or ("Layout" if data.get("type") == 0 else ""),
            redirect=data.get("redirect"),
            icon=data.get("icon"),
            type=int(data.get("type", 1)),
            hidden=bool(data.get("hidden", False)),
            always_show=bool(data.get("alwaysShow", False)),
            sort=int(data.get("sort", 0)),
        )

        # 如果是按钮类型，自动创建权限标识
        if router.type == 2:  # 按钮
            perm_code = data.get("permissionCode", f"{router.name.lower()}:view")
            Permission.objects.get_or_create(
                router=router,
                code=perm_code,
                defaults={"name": perm_code.split(":")[-1]}
            )

        return ApiResponse.success({
            "id": router.id,
            "msg": "创建成功"
        })


class MenuUpdateView(APIView):
    """编辑菜单"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, pk):
        try:
            router = Router.objects.get(pk=pk)
        except Router.DoesNotExist:
            return ApiResponse.error("菜单不存在")

        data = request.data
        parent_id = data.get("parent")
        router.parent = Router.objects.get(id=parent_id) if parent_id and parent_id != "null" else None
        router.title = data["title"]
        router.name = data["name"]
        router.path = data["path"]
        router.component = data.get("component") or ("Layout" if data.get("type") == 0 else "")
        router.redirect = data.get("redirect")
        router.icon = data.get("icon")
        router.type = int(data.get("type", 1))
        router.hidden = bool(data.get("hidden", False))
        router.always_show = bool(data.get("alwaysShow", False))
        router.sort = int(data.get("sort", 0))
        router.save()

        # 更新按钮权限标识
        if router.type == 2:
            perm_code = data.get("permissionCode", f"{router.name.lower()}:view")
            perm, _ = Permission.objects.update_or_create(
                router=router,
                defaults={"code": perm_code, "name": perm_code.split(":")[-1]}
            )

        return ApiResponse.success("更新成功")


class MenuDeleteView(APIView):
    """删除菜单（级联删除子菜单和权限）"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, pk):
        try:
            router = Router.objects.get(pk=pk)
        except Router.DoesNotExist:
            return ApiResponse.error("菜单不存在")

        if router.type == 0 and router.children.exists():
            return ApiResponse.error("请先删除子菜单")

        # 删除关联的权限
        router.permissions.all().delete()
        router.delete()

        return ApiResponse.success("删除成功")


# 可选：获取所有图标列表（前端图标选择器用）
class IconListView(APIView):
    def get(self, request):
        icons = [
            "home", "lock", "user", "menu", "document", "setting", "warning", "info",
            "success", "error", "edit", "delete", "plus", "search", "refresh",
            "upload", "download", "picture", "video-play", "connection", "monitor"
        ]
        return ApiResponse.success(icons)