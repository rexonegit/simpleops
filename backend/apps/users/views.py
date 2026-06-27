from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.utils.response import ApiResponse

from apps.logs.models import LoginLog
from django.contrib.auth import authenticate
from django.core.files.images import get_image_dimensions
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        ip = self.get_client_ip(request)

        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            LoginLog.objects.create(
                username=username,
                ip=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status=True
            )
            return ApiResponse.success({
                'accessToken': str(refresh.access_token),
                'refreshToken': str(refresh),
                'username': user.username,
                'avatar': user.avatar.url if user.avatar else ''
            }, "登录成功")
        else:
            LoginLog.objects.create(
                username=username or 'unknown',
                ip=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status=False
            )
            return ApiResponse.login_error("用户名或密码错误")

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):  # 改为 get
        user = request.user
        permissions = set()
        for role in user.roles.all():
            for perm in role.permissions.all():
                permissions.add(perm.code)

        data = {
            "id": user.id,
            "username": user.username,
            "avatar": user.avatar.url if user.avatar else "",
            "phone": user.phone or "",
            "email": getattr(user, 'email', '') or "",
            "create_time": user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            "last_login": user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else None,
            "roles": [role.code for role in user.roles.all()],
            "roleNames": [role.name for role in user.roles.all()],  # Added roleNames
            "permissions": list(permissions),
        }
        return ApiResponse.success(data)


class UploadAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return ApiResponse.error("请选择文件")
        if not file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            return ApiResponse.error("不支持的文件格式")
        if file.size > 2 * 1024 * 1024:
            return ApiResponse.error("图片不能超过2MB")

        request.user.avatar = file
        request.user.save()
        return ApiResponse.success({"avatar": request.user.avatar.url})


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone = request.data.get('phone')
        email = request.data.get('email')

        user = request.user
        # 简单校验，实际项目可以使用Serializer
        if phone:
            # 这里假设User模型有phone字段
            user.phone = phone
        if email:
            user.email = email
        user.save()

        return ApiResponse.success("保存成功")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('oldPassword')
        new_password = request.data.get('newPassword')
        confirm_password = request.data.get('confirmPassword')

        if not all([old_password, new_password, confirm_password]):
            return ApiResponse.error("参数不完整")

        if new_password != confirm_password:
            return ApiResponse.error("两次密码输入不一致")

        user = request.user
        if not user.check_password(old_password):
            return ApiResponse.error("原密码错误")

        user.set_password(new_password)
        user.save()

        return ApiResponse.success("密码修改成功")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # JWT 是无状态的，退出登录只需要前端删除 token 即可
        # 后端什么都不用做，直接返回成功
        return ApiResponse.success("退出登录成功")