from django.urls import path
from .views.router import NavigateView

from .views  import  user, role, menu

urlpatterns = [
    path('navigate/', NavigateView.as_view(), name='navigate'),

    # 用户管理
    path('user/list/', user.UserListView.as_view()),
    path('user/create/', user.UserCreateView.as_view()),
    path('user/update/<int:pk>/', user.UserUpdateView.as_view()),
    path('user/delete/', user.UserDeleteView.as_view()),
    path('user/reset-password/', user.ResetPasswordView.as_view()),
    path('user/assign-roles/', user.AssignRolesView.as_view()),
    path('user/roles/', user.RoleSelectView.as_view()),

    # 角色管理
    path('role/list/', role.RoleListView.as_view()),
    path('role/create/', role.RoleCreateView.as_view()),
    path('role/update/<int:pk>/', role.RoleUpdateView.as_view()),
    path('role/delete/<int:pk>/', role.RoleDeleteView.as_view()),
    path('role/permissions/<int:pk>/', role.RolePermissionsView.as_view()),
    path('role/assign-permissions/', role.AssignPermissionsView.as_view()),

    # 菜单管理接口
    path('tree/', menu.MenuTreeView.as_view()),  # 改成 tree/
    path('create/', menu.MenuCreateView.as_view()),
    path('update/<int:pk>/', menu.MenuUpdateView.as_view()),
    path('delete/<int:pk>/', menu.MenuDeleteView.as_view()),
    path('icons/', menu.IconListView.as_view()),

]