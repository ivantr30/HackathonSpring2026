from django.shortcuts import render, redirect
from .forms import RegistrationForm, SessionForm, CustomLoginForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group 
from .models import Audio, Video, MediatekElement, Playlist
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
# Create your views here.

def user_is_host(request):
    return request.user.groups.filter(name="Ведущий").exists() or request.user.is_superuser
def user_is_admin(request):
    return request.user.groups.filter(name="Админ").exists() or request.user.is_superuser

@login_required
def player(request):
    return render(request, 'player.html')
@login_required
def host(request):
    if not user_is_host(request):
        return redirect('player')
    
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
    playlist_elements = playlist.elements.all() if playlist else []

    return render(request, 'host.html', {"form" : None, 
                                         "has_session" : True,
                                         "is_playing" : request.user.sessions.all()[0].is_playing, 
                                         "my_video" : my_video,
                                         "my_audio" : my_audio,
                                         "playlist_elements" : playlist_elements})

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
    return redirect('player')


def register(request):

    if request.user.is_authenticated:
        return redirect('player')
    
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
        return redirect('player')
    
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
    return player(request)

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
        return redirect('player')
@login_required
def add_to_playlist(request, item_id):
    if not user_is_host(request):
        return redirect("player")
    if request.method == "POST":
        item = get_object_or_404(MediatekElement, id=item_id, owner=request.user)
        
        playlist, created = Playlist.objects.get_or_create(owner=request.user, title="Очередь эфира")
        
        playlist.elements.add(item)
        
    return redirect('host')

@login_required
def remove_from_playlist(request, item_id):
    if not user_is_host(request):
        return redirect("player")
    if request.method == "POST":
        item = get_object_or_404(MediatekElement, id=item_id, owner=request.user)
        playlist = Playlist.objects.filter(owner=request.user, title="Очередь эфира").first()
        
        if playlist:
            playlist.elements.remove(item)
            
    return redirect('host')
