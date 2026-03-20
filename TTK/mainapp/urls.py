from django.urls import include, path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path("", views.player, name="player"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
]
