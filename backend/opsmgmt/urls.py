from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertRecordViewSet

router = DefaultRouter()
router.register(r'alerts', AlertRecordViewSet, basename='alertrecord')

urlpatterns = [
    path('opsmgmt/', include(router.urls)),
]
