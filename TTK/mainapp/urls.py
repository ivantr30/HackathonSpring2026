from django.urls import include, path
from django.shortcuts import redirect
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", views.player, name="player"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    
    path("host/", views.host_dashboard, name="host_dashboard"),
    path("host/upload_media/", views.upload_media, name="upload_media"),
    path("host/msg_status/<int:msg_id>/", views.change_msg_status, name="change_msg_status"),
    path("host/broadcast_voice/", views.broadcast_voice, name="broadcast_voice"),
    
    path("user/send_message/", views.send_user_message, name="send_user_message"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
