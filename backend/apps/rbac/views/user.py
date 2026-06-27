# apps/rbac/views/user.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.utils.response import ApiResponse
from apps.users.models import User
from apps.rbac.models import Role
from django.db import transaction
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import make_password


class UserListView(APIView):
    """用户列表（分页 + 搜索）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        username = request.query_params.get("username", "").strip()
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("size", 20))

        queryset = User.objects.all().order_by('-id')
        if username:
            queryset = queryset.filter(username__contains=username)

        total = queryset.count()
        start = (page - 1) * size
        end = start + size
        users = queryset[start:end]

        data = []
        for u in users:
            data.append({
                "id": u.id,
                "username": u.username,
                "phone": u.phone or "",
                "avatar": u.avatar.url if u.avatar else "",
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "roles": [r.name for r in u.roles.all()],
                "date_joined": u.date_joined.strftime("%Y-%m-%d %H:%M:%S")
            })

        return ApiResponse.success({
            "list": data,
            "total": total
        })


class UserCreateView(APIView):
    """新增用户"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        phone = request.data.get("phone", "")
        role_ids = request.data.get("roles", [])

        if User.objects.filter(username=username).exists():
            return ApiResponse.error("用户名已存在")

        if not password or len(password) < 6:
            return ApiResponse.error("密码长度必须大于等于6位")

        user = User.objects.create(
            username=username,
            phone=phone,
            password=make_password(password),
            is_active=True
        )

        if role_ids:
            roles = Role.objects.filter(id__in=role_ids)
            user.roles.set(roles)

        return ApiResponse.success({"msg": "创建成功", "id": user.id})


class UserUpdateView(APIView):
    """编辑用户（不能修改超级管理员）"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return ApiResponse.error("用户不存在")

        if user.is_superuser:
            return ApiResponse.error("禁止修改超级管理员")

        username = request.data.get("username", user.username)
        phone = request.data.get("phone", user.phone or "")
        is_active = request.data.get("is_active", user.is_active)
        role_ids = request.data.get("roles", [])

        if User.objects.filter(username=username).exclude(pk=pk).exists():
            return ApiResponse.error("用户名已存在")

        user.username = username
        user.phone = phone
        user.is_active = bool(is_active)
        user.save()

        if role_ids is not None:
            roles = Role.objects.filter(id__in=role_ids)
            user.roles.set(roles)

        return ApiResponse.success("更新成功")


class UserDeleteView(APIView):
    """删除用户（禁止删除超级管理员）"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        ids = request.data.get("ids", [])
        if not ids:
            return ApiResponse.error("请选中要删除的用户")

        # 禁止删除超级管理员
        superusers = User.objects.filter(id__in=ids, is_superuser=True)
        if superusers.exists():
            return ApiResponse.error("禁止删除超级管理员")

        User.objects.filter(id__in=ids).delete()
        return ApiResponse.success("删除成功")


class ResetPasswordView(APIView):
    """重置密码为 123456"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get("id")
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return ApiResponse.error("用户不存在")

        if user.is_superuser:
            return ApiResponse.error("禁止重置超级管理员密码")

        user.set_password("123456")
        user.save()
        return ApiResponse.success("密码已重置为 123456")


class AssignRolesView(APIView):
    """给用户分配角色"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get("userId")
        role_ids = request.data.get("roleIds", [])

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return ApiResponse.error("用户不存在")

        if user.is_superuser:
            return ApiResponse.error("超级管理员角色由系统分配")

        roles = Role.objects.filter(id__in=role_ids)
        user.roles.set(roles)
        return ApiResponse.success("角色分配成功")


class RoleSelectView(APIView):
    """获取所有角色（用于下拉框）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = Role.objects.all()
        data = [{"value": r.id, "label": r.name} for r in roles]
        return ApiResponse.success(data)