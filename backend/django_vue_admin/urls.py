from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(title="Vue Admin Better API", default_version='v1', description="完整RBAC系统"),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 认证相关
    path('api/auth/', include('apps.users.urls')),

    # 菜单路由
    path('api/menu/', include('apps.rbac.urls')),

    # 日志
    path('api/logs/', include('apps.logs.urls')),

    # Token 刷新
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Swagger 文档
    re_path(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('api/', include('aliyun.urls')),
    path('api/', include('datacenter.urls')),
    path('api/', include('cmdb.urls')),
    path('api/', include('opsmgmt.urls')),
]

# 开发环境提供 media 文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
