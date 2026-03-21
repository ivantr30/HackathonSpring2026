from django.urls import include, path
from django.shortcuts import redirect
from . import views


urlpatterns = [
    path("", views.player, name="player"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("admin/users", views.user_management, name="users"),
    path("admin/users/<int:user_id>/edit", views.edit_user, name="edit_user"),
    path("admin/users/<int:user_id>/change-password", views.change_password, name="change_password"),
    path("admin/users/<int:user_id>/assign-roles", views.assign_roles, name="assign_roles"),
    path("admin/users/<int:user_id>/delete", views.delete_user, name="delete_user"),
]
