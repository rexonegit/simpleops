from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NetworkSegmentViewSet, IPAddressViewSet, cmdbdatabaseViewSet

router = DefaultRouter()
router.register(r'ip-addresses', IPAddressViewSet, basename='ipaddress')
router.register(r'ip-segments', NetworkSegmentViewSet, basename='networksegment')
router.register(r'cmdbdatabase', cmdbdatabaseViewSet, basename='cmdbdatabase')

urlpatterns = [
    path('', include(router.urls)),
]
