#
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import ProjectBareMetalViewSet, ProjectNetworkDeviceViewSet, ProjectVMwareViewSet, ProjectProxmoxViewSet, VMwareVMViewSet, ProxmoxVMViewSet

router = DefaultRouter()
router.register(r'projectbaremetal', ProjectBareMetalViewSet, basename='projectbaremetal')
router.register(r'projectnetworkdevice', ProjectNetworkDeviceViewSet, basename='projectnetworkdevice')
router.register(r'projectvmware', ProjectVMwareViewSet, basename='projectvmware')
router.register(r'projectproxmox', ProjectProxmoxViewSet, basename='projectproxmox')
router.register(r'vmware', VMwareVMViewSet, basename='vmware')
router.register(r'proxmox', ProxmoxVMViewSet, basename='proxmox')


urlpatterns = [
    path('', include(router.urls)),
]



