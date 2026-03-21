from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Create your views here.
@login_required
def player(request):
    session = Session.objects.first()
    return render(request, 'player.html', {'session': session})

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
        form = AuthenticationForm(request.POST, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            return redirect_if_user_wasnt_auth(request, user)
    else:
        form = AuthenticationForm()

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
    
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import Session, Message, Audio, Video, User, TextMessage, VoiceMessage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@login_required
def host_dashboard(request):
    session = Session.objects.first()
    
    # Сообщения
    active_msgs = Message.objects.filter(state__in=['new', 'in_progress']).order_by('-id')
    archived_msgs = Message.objects.filter(state='done').order_by('-id')
    
    # Медиатека
    my_audio = Audio.objects.filter(owner=request.user)
    my_video = Video.objects.filter(owner=request.user)

    context = {
        'session': session,
        'active_msgs': active_msgs,
        'archived_msgs': archived_msgs,
        'my_audio': my_audio,
        'my_video': my_video,
    }
    return render(request, 'host_dashboard.html', context)

@login_required
def upload_media(request):
    if request.method == "POST":
        file = request.FILES.get('media_file')
        name = request.POST.get('name', 'Без названия')
        file_type = request.POST.get('file_type')

        if file and file_type == 'audio':
            Audio.objects.create(owner=request.user, name=name, audio_file=file)
        elif file and file_type == 'video':
            Video.objects.create(owner=request.user, name=name, video_file=file)
    return redirect('host_dashboard')

@csrf_exempt  
@login_required
def change_msg_status(request, msg_id):
    if request.method == "POST":
        msg = get_object_or_404(Message, id=msg_id)
        msg.state = request.POST.get('status')
        msg.save()
    return redirect('host_dashboard')

@csrf_exempt
@login_required
def broadcast_voice(request):
    """Ведущий записал голос -> сохраняем -> командуем плееру слушателя включить"""
    if request.method == 'POST':
        voice_file = request.FILES.get('voice_blob')
        if voice_file:
            # Сохраняем как обычное аудио в медиатеку
            audio_obj = Audio.objects.create(owner=request.user, name="🔴 Live Эфир", audio_file=voice_file)
            
            # Отправляем сигнал по WebSocket всем слушателям!
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'live_stream',
                {
                    'type': 'stream_event',
                    'event_type': 'play_host_voice',
                    'payload': {'url': audio_obj.audio_file.url}
                }
            )
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'bad'}, status=400)
@csrf_exempt
@login_required
def send_user_message(request):
    """Слушатель отправляет текст или голос ведущему"""
    if request.method == "POST":
        # Берем первого суперюзера как Ведущего (или замени логику поиска хоста)
        host_user = User.objects.filter(is_superuser=True).first()
        
        msg_id = None
        msg_text = None
        msg_voice_url = None

        # 1. Сохраняем ТЕКСТ
        if 'text' in request.POST:
            new_msg = TextMessage.objects.create(
                sender=request.user, host=host_user, text=request.POST['text']
            )
            msg_id = new_msg.id
            msg_text = new_msg.text

        # 2. Сохраняем ГОЛОСОВОЕ
        elif 'voice_blob' in request.FILES:
            new_msg = VoiceMessage.objects.create(
                sender=request.user, host=host_user, voice_message=request.FILES['voice_blob']
            )
            msg_id = new_msg.id
            msg_voice_url = new_msg.voice_message.url

        # 3. МАГИЯ ВЕБСОКЕТОВ: Отправляем уведомление Ведущему
        if msg_id:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'live_stream',
                {
                    'type': 'stream_event',
                    'event_type': 'new_message',
                    'payload': {
                        'id': msg_id,
                        'sender': request.user.username,
                        'text': msg_text,
                        'voice_url': msg_voice_url
                    }
                }
            )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'bad'}, status=400)