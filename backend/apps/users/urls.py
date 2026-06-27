from django.urls import path
from .views import LoginView, UserInfoView, UploadAvatarView, UpdateProfileView, ChangePasswordView,LogoutView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('userInfo/', UserInfoView.as_view()),
    path('upload/avatar/', UploadAvatarView.as_view()),
    path('update/info/', UpdateProfileView.as_view()),
    path('update/password/', ChangePasswordView.as_view()),
    path('logout/', LogoutView.as_view()),
]