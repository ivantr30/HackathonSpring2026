from django.urls import include, path
from django.shortcuts import redirect
from . import views

app_name = "users"

urlpatterns = [
    path("", lambda request: redirect("player"), name="root"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
