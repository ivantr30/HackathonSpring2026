from django.urls import include, path
from django.shortcuts import redirect
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", views.player, name="player"),
    path("host", views.host, name="host"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
