# apps/rbac/views/router.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.utils.response import ApiResponse
from apps.rbac.models import Router


class NavigateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        all_routers = Router.objects.all().select_related('parent').order_by('sort', 'id')

        if user.is_superuser:
            routers = Router.objects.filter(type__in=[0, 1]).order_by('sort', 'id')
        else:
            # 关键修复！不仅要包含直接分配的菜单，还要包含它们的祖先目录！
            menu_ids = set()
            for role in user.roles.all():
                direct_menus = role.menus.filter(type__in=[0, 1])
                for menu in direct_menus:
                    current = menu
                    while current:
                        menu_ids.add(current.id)
                        current = current.parent
            routers = Router.objects.filter(id__in=menu_ids).order_by('sort', 'id')
        router_dict = {r.id: r for r in routers}

        def build_tree(parent=None):
            tree = []
            items = [r for r in routers if (parent is None and r.parent_id is None) or (parent and r.parent_id == parent.id)]

            for item in items:
                # === 关键修改1：component 直接拼接前缀，不做任何处理 ===
                raw_component = (item.component or "").strip()
                if item.type == 1:  # 菜单
                    if raw_component:
                        if raw_component.startswith('@/'):
                            component = raw_component
                        elif raw_component.startswith('/'):
                            component = '@/views' + raw_component
                        else:
                            component = '@/views/' + raw_component
                    else:
                        component = ""
                elif item.type == 0:  # 目录
                    # 判断是否有孙子节点，决定用 EmptyLayout 还是 Layout
                    has_grandchild = any(
                        c.children.filter(id__in=router_dict).exists()
                        for c in item.children.all() if c.id in router_dict
                    )
                    component = "EmptyLayout" if has_grandchild else "Layout"
                elif item.type == 3:  # 外链
                    component = "external"
                else:
                    component = ""

                # === path 处理：根节点加 /，子节点去掉开头的 / ===
                if parent is None:
                    path = item.path if item.path.startswith('/') else f'/{item.path}'
                else:
                    path = item.path.lstrip('/')

                node = {
                    "path": path,
                    "name": item.name,
                    "component": component,
                    "hidden": item.hidden,
                    "meta": {
                        "title": item.title,
                        "icon": item.icon or "folder",
                        "hidden": item.hidden,
                        "affix": item.affix,
                        "keepAlive": item.keep_alive,
                        "badge": item.badge,
                        "permissions": [p.code for p in item.permissions.all()]
                    }
                }

                # redirect：目录和外链支持，值直接使用数据库中的 redirect 字段（建议存 name 如 "index"）
                if item.type in [0, 3] and item.redirect:
                    node["redirect"] = item.redirect

                if item.type == 0:
                    child_count = sum(1 for c in item.children.all() if c.id in router_dict)
                    node["alwaysShow"] = item.always_show or child_count > 0

                if item.type == 3:
                    node["meta"]["link"] = item.path

                children = build_tree(item)
                if children or item.type == 0:
                    node["children"] = children

                tree.append(node)

            return tree

        routes = build_tree()

        # ============================================
        # 关键修改：将首页路由转换为嵌套结构
        # ============================================
        def transform_to_nested_structure(routes):
            """将平铺的路由结构转换为嵌套的 Layout > Index 结构"""
            # 查找首页路由
            index_route = None
            other_routes = []

            for route in routes:
                if route.get("name") == "Index":
                    index_route = route
                else:
                    other_routes.append(route)

            # 如果找到首页路由，重构为嵌套结构
            if index_route:
                # 修改首页的 path 为 "index"（去掉开头的 /）
                index_route["path"] = "index"

                # 创建根路由
                root_route = {
                    "path": "/",
                    "component": "Layout",
                    "redirect": "index",  # 使用 name 进行重定向
                    "children": [index_route]
                }

                # 返回重构后的路由列表
                return [root_route] + other_routes

            return routes

        # 应用转换
        routes = transform_to_nested_structure(routes)

        return ApiResponse.success(routes)