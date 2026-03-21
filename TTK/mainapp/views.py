from django.shortcuts import render, redirect
from .forms import RegistrationForm, SessionForm, CustomLoginForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group 
from .models import Audio, Video, MediatekElement, Playlist, Session
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
import random
# Create your views here.

def user_is_host(request):
    return request.user.groups.filter(name="Ведущий").exists() or request.user.is_superuser
def user_is_admin(request):
    return request.user.groups.filter(name="Админ").exists() or request.user.is_superuser

from django.shortcuts import render, get_object_or_404

@login_required
def player_lobby(request):
    active_sessions = Session.objects.all().order_by('-id')
    return render(request, 'player_lobby.html', {'active_sessions': active_sessions})

@login_required
def player_room(request, session_id):
    selected_session = get_object_or_404(Session, id=session_id)
    return render(request, 'player.html', {'session': selected_session})
@login_required
def host(request):
    if not user_is_host(request):
        return redirect('player_lobby')
    
    if not request.user.sessions.exists():
        if request.method == "POST":
            form = SessionForm(request.POST)
            if form.is_valid():
                new_session = form.save(commit=False)
                new_session.owner = request.user
                new_session.save()
            else:
                return
            return render(request, 'host.html', {"has_session" : True, "is_playing" : request.user.sessions.all()[0].is_playing})
        else:
            form = SessionForm()
            return render(request, 'host.html', {'form' : form, "has_session" : False, "is_playing" : False})
    my_audio = Audio.objects.filter(owner=request.user).order_by('-id')
    my_video = Video.objects.filter(owner=request.user).order_by('-id')
    playlist = Playlist.objects.filter(owner=request.user, title="Очередь эфира").first()
    
    playlist_elements = list(playlist.elements.all()) if playlist else []

    current_session = request.user.sessions.first()

    if current_session and current_session.is_shuffled:
        shuffled_ids = request.session.get('shuffled_ids', [])
        if shuffled_ids:
            # Сортируем треки точно в том порядке, который запомнили при нажатии кнопки Shuffle
            playlist_elements.sort(key=lambda x: shuffled_ids.index(x.id) if x.id in shuffled_ids else 999)

    return render(request, 'host.html', {
        "form" : None, 
        "has_session" : True,
        "is_playing" : current_session.is_playing if current_session else False, 
        "session": current_session,
        "my_video" : my_video,
        "my_audio" : my_audio,
        "playlist_elements" : playlist_elements
    })

@login_required
def upload_media(request):
    if request.method == "POST" and user_is_host(request):
        file = request.FILES.get('media_file')
        name = request.POST.get('name', "Без названия")
        file_type = request.POST.get('file_type')

        if file:
            try:
                if file_type == 'audio':
                    new_media = Audio(
                        owner=request.user, 
                        name=name, 
                        audio_file=file
                    )
                elif file_type == 'video':
                    new_media = Video(
                        owner=request.user, 
                        name=name, 
                        video_file=file
                    )
                new_media.full_clean() 
                new_media.save()   
                messages.success(request, f"Файл '{name}' успешно загружен!")
            except ValidationError as e:
                 for field, error_list in e.message_dict.items():
                    for error in error_list:
                        messages.error(request, f"Ошибка загрузки: {error}")

        return redirect('host')
    return redirect('player_lobby')


def register(request):

    if request.user.is_authenticated:
        return redirect('player_lobby')
    
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            listener, created = Group.objects.get_or_create(name="Слушатель")
            user.groups.add(listener)
            return redirect_if_user_wasnt_auth(request, user)
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):

    if request.user.is_authenticated:
        return redirect('player_lobby')
    
    if request.method == "POST":
        form = CustomLoginForm(request.POST, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            return redirect_if_user_wasnt_auth(request, user)
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})
def logout_view(request):
    if request.method == 'POST':
        logout(request) 
        return redirect('login') 
    return redirect("player_lobby")

def redirect_if_user_wasnt_auth(request, user):
    login(request, user) 
    next_url = request.POST.get('next') or request.GET.get('next')

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)
    else:
        return redirect('player_lobby')
@login_required
def add_to_playlist(request, item_id):
    if not user_is_host(request):
        return redirect("player_lobby")
    if request.method == "POST":
        item = get_object_or_404(MediatekElement, id=item_id, owner=request.user)
        
        playlist, created = Playlist.objects.get_or_create(owner=request.user, title="Очередь эфира")
        
        playlist.elements.add(item)
        
    return redirect('host')

@login_required
def remove_from_playlist(request, item_id):
    if not user_is_host(request):
        return redirect("player_lobby")
    if request.method == "POST":
        item = get_object_or_404(MediatekElement, id=item_id, owner=request.user)
        playlist = Playlist.objects.filter(owner=request.user, title="Очередь эфира").first()
        
        if playlist:
            playlist.elements.remove(item)
            
    return redirect('host')
@login_required
def toggle_shuffle(request):
    if request.method == "POST":
        session = request.user.sessions.first()
        if session:
            # Переключаем кнопку
            session.is_shuffled = not session.is_shuffled
            session.save()
            
            if session.is_shuffled:
                # Включили Shuffle: берем треки, перемешиваем их ID и запоминаем!
                playlist = Playlist.objects.filter(owner=request.user, title="Очередь эфира").first()
                if playlist:
                    # Достаем список ID (например: [1, 2, 3])
                    ids = list(playlist.elements.values_list('id', flat=True))
                    random.shuffle(ids) # Перемешиваем: [3, 1, 2]
                    
                    # Сохраняем в память (куки сервера)
                    request.session['shuffled_ids'] = ids
            else:
                # Выключили Shuffle: удаляем память
                if 'shuffled_ids' in request.session:
                    del request.session['shuffled_ids']

    return redirect('host')
@login_required
def toggle_loop(request):
    if request.method == "POST":
        session = request.user.sessions.first()
        if session:
            session.is_looping = not session.is_looping
            session.save()
    return redirect('host')
@login_required
def delete_media(request, media_type, media_id):
    # Разрешаем удалять только через POST-запрос (для безопасности)
    if request.method == "POST":
        
        # Определяем, в какой таблице искать
        if media_type == 'audio':
            # Находим файл, причем ТОЛЬКО если он принадлежит текущему ведущему!
            media_item = get_object_or_404(Audio, id=media_id, owner=request.user)
            # Физически удаляем файл с диска
            if media_item.audio_file:
                media_item.audio_file.delete(save=False)
                
        elif media_type == 'video':
            media_item = get_object_or_404(Video, id=media_id, owner=request.user)
            if media_item.video_file:
                media_item.video_file.delete(save=False)
        else:
            return redirect('host')

        # Удаляем запись из базы данных (при этом трек автоматически исчезнет и из плейлиста, если он там был)
        name = media_item.name
        media_item.delete()
        
        messages.success(request, f"Файл '{name}' успешно удален из медиатеки.")
        
    return redirect('host')