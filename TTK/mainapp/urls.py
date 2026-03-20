from django.urls import include, path
from django.shortcuts import redirect
from . import views

app_name = "mainapp"

urlpatterns = [
    path("", views.player, name="player"),
    path("users/", include("mainapp.users.urls", namespace="users")),
]
