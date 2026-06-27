# apps/logs/middleware.py
import time
import json
from django.utils.deprecation import MiddlewareMixin
from apps.logs.models import OperationLog, LoginLog
from apps.utils.response import ApiResponse
import logging

logger = logging.getLogger(__name__)


class OperationLogMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        request._start_time = time.time()

    def process_response(self, request, response):
        # 跳过登录接口、静态文件、drf-yasg 文档
        if any([
            request.path.startswith('/api/auth/'),
            request.path.startswith('/media/'),
            request.path.startswith('/static/'),
            request.path.startswith('/docs/'),
            request.path.startswith('/swagger/'),
            request.method == 'OPTIONS'
        ]):
            return response

        user = request.user if request.user.is_authenticated else None
        if not user:
            return response

        try:
            duration = int((time.time() - getattr(request, '_start_time', time.time())) * 1000)
            
            # 安全获取请求体（兼容 DRF 已消耗数据流的情况）
            body = self.get_request_body_safe(request)
            if len(body) > 500:
                body = body[:500] + "..."

            # 自动推断操作类型
            method = request.method
            path = request.path
            action_map = {
                'POST': '创建',
                'PUT': '更新',
                'PATCH': '更新',
                'DELETE': '删除',
            }
            action = action_map.get(method, '查询')

            OperationLog.objects.create(
                user=user,
                ip=self.get_client_ip(request),
                method=method,
                path=path,
                status_code=response.status_code,
                duration=duration,
                action=action + self.guess_model(path),
                request_body=body,
                response_body=response.content.decode('utf-8')[:1000] if hasattr(response, 'content') else ''
            )
        except Exception as e:
            logger.error(f"记录操作日志失败: {e}")

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'

    def guess_model(self, path):
        mapping = {
            '/user/': '用户',
            '/role/': '角色',
            '/router/': '菜单',
            '/permission/': '权限',
        }
        for k, v in mapping.items():
            if k in path:
                return v
        return ''

    def get_request_body_safe(self, request):
        """安全获取请求体内容（兼容 DRF 已消耗数据流的情况）
        
        DRF 在处理 POST/PUT 请求时会先读取 request.data，消耗掉 request.body 流，
        此后再直接读取 request.body 会报错：
        "You cannot access body after reading from request's data stream"
        
        解决方案：优先使用 request.data（DRF 已解析的数据），其次使用 request._body（Django 缓存）
        """
        try:
            # 方案1：优先使用 DRF 已解析的 request.data
            if hasattr(request, 'data') and request.data:
                data = request.data
                # 密码脱敏
                if isinstance(data, dict) and 'password' in data:
                    data = data.copy()
                    data['password'] = '******'
                return json.dumps(data, ensure_ascii=False, default=str)
            
            # 方案2：其次使用 Django 缓存的 request._body
            if hasattr(request, '_body') and request._body:
                return request._body.decode('utf-8', errors='ignore')
            
            # 方案3：尝试 GET/POST 参数
            params = {**request.GET.dict(), **request.POST.dict()}
            if params:
                return json.dumps(params, ensure_ascii=False)
            
            return ''
        except Exception:
            return '<unable to read body>'

    def process_request(self, request):
        request._start_time = time.time()
