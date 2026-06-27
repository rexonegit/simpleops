# apps/logs/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.utils.response import ApiResponse
from apps.logs.models import LoginLog, OperationLog
from django.utils import timezone
from datetime import timedelta

class LoginLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("size", 20))
        username = request.query_params.get("username", "").strip()

        queryset = LoginLog.objects.all()
        if username:
            queryset = queryset.filter(username__contains=username)

        total = queryset.count()
        start = (page - 1) * size
        logs = queryset[start:start + size]

        data = [{
            "id": log.id,
            "username": log.username,
            "ip": log.ip,
            "user_agent": log.user_agent[:50] + "..." if len(log.user_agent) > 50 else log.user_agent,
            "status": "成功" if log.status else "失败",
            "created_at": timezone.localtime(log.created_at).strftime("%Y-%m-%d %H:%M:%S")  # 转换本地时间
        } for log in logs]

        return ApiResponse.success({
            "list": data,
            "total": total
        })

class OperationLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("size", 20))

        queryset = OperationLog.objects.select_related('user').all()
        total = queryset.count()
        start = (page - 1) * size
        logs = queryset[start:start + size]

        data = [{
            "id": log.id,
            "username": log.user.username if log.user else "系统",
            "ip": log.ip,
            "method": log.method,
            "path": log.path,
            "action": log.action,
            "status_code": log.status_code,
            "duration": log.duration,
            "created_at": timezone.localtime(log.created_at).strftime("%Y-%m-%d %H:%M:%S")  # 转换本地时间
        } for log in logs]

        return ApiResponse.success({
            "list": data,
            "total": total
        })