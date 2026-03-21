from django.urls import include, path
from django.shortcuts import redirect
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [ 
    path("", views.player_lobby, name="player_lobby"), 
    path("player/<int:session_id>/", views.player_room, name="player_room"), 
    path("host", views.host, name="host"),
    path("host/upload-media", views.upload_media, name="upload_media"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path('host/playlist/add/<int:item_id>/', views.add_to_playlist, name='add_to_playlist'),
    path('host/playlist/remove/<int:item_id>/', views.remove_from_playlist, name='remove_from_playlist'),
    path('host/toggle-shuffle/', views.toggle_shuffle, name='toggle_shuffle'),
    path('host/toggle-loop/', views.toggle_loop, name='toggle_loop'),
    path('host/delete-media/<str:media_type>/<int:media_id>/', views.delete_media, name='delete_media'),
    path('host/upload-voice/', views.upload_voice_message, name='upload_voice_message'),
    path('player/send-message/', views.send_message, name='send_message'),
    path('host/change-msg-status/<int:msg_id>/', views.change_msg_status, name='change_msg_status'),
    path('host/delete-session/', views.delete_session, name='delete_session'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
