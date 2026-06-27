# apps/logs/urls.py
from django.urls import path
from .views import LoginLogListView, OperationLogListView

urlpatterns = [
    path('login-log/list/', LoginLogListView.as_view()),
    path('operation-log/list/', OperationLogListView.as_view()),
]