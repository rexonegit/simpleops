# aliyun/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import AliyunOSSViewSet, AliyunRAMUserViewSet, AliyunECSListViewSet, ProjectAliyunecsViewSet, \
    AliyunDomainViewSet, AliyunSLBViewSet, ProjectAliyunSLBViewSet, AliyunRDSViewSet, ProjectAliyunRDSViewSet, AliyunEIPViewSet, AliyunWAFViewSet, AliyunNASViewSet, ProjectAliyunNASViewSet, \
    AliyunSNATEntryViewSet, ProjectAliyunDomainViewSet, ProjectAliyunSLSViewSet

router = DefaultRouter()
router.register(r'oss', AliyunOSSViewSet, basename='aliyun-oss')
router.register(r'ram', AliyunRAMUserViewSet, basename='aliyun-ram')
router.register(r'ecs', AliyunECSListViewSet, basename='aliyunecs')
router.register(r'projectaliyunecs', ProjectAliyunecsViewSet, basename='projectaliyunecs')
router.register(r'domain', AliyunDomainViewSet, basename='aliyun-domain')
router.register(r'projectaliyundomain', ProjectAliyunDomainViewSet, basename='projectaliyundomain')
router.register(r'api/dns-records', views.AliyunDNSRecordViewSet, basename='dnsrecord')

router.register(r'slb', AliyunSLBViewSet, basename='aliyun-slb')
router.register(r'projectaliyunslb', ProjectAliyunSLBViewSet, basename='projectaliyunslb')
router.register(r'rds', AliyunRDSViewSet, basename='aliyun-rds')
router.register(r'projectaliyunrds', ProjectAliyunRDSViewSet, basename='projectaliyunrds')
router.register(r'eip', AliyunEIPViewSet, basename='aliyun-eip')
router.register(r'waf', AliyunWAFViewSet, basename='aliyun-waf')
router.register(r'nas', AliyunNASViewSet, basename='aliyun-nas')
router.register(r'projectaliyunnas', ProjectAliyunNASViewSet, basename='projectaliyunnas')
router.register(r'snat', AliyunSNATEntryViewSet, basename='snat')
router.register(r'sls', views.AliyunSLSViewSet, basename='sls')
router.register(r'projectaliyunsls', ProjectAliyunSLSViewSet, basename='projectaliyunsls')
router.register(r'security-groups', views.AliyunSecurityGroupViewSet, basename='security-group')
router.register(r'security-group-rules', views.AliyunSecurityGroupRuleViewSet, basename='security-group-rule')

urlpatterns = [
    path('', include(router.urls)),
    # 域名 资产相关路由

    path('oss/buckets/<str:bucket_name>/', views.OSSBucketDetailView.as_view(), name='oss-bucket-detail'),
]
