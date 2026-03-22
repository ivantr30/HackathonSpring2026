from django.shortcuts import render, redirect, get_object_or_404
from .forms import (
    RegistrationForm,
    SessionForm,
    CustomLoginForm,
    UserFilterForm,
    UserEditForm,
    UserAdminPasswordChangeForm,
    UserRoleAssignmentForm,
    UserDeleteForm,
)
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group
from .models import Audio, Video, MediatekElement, Playlist, Session, VoiceMessage, TextMessage, Message
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

import random
from django.contrib.auth.models import Group
from django.contrib import messages
import datetime

User = get_user_model()


# Create your views here.


def user_is_host(request):
    return request.user.groups.filter(name="Ведущий").exists() or request.user.is_superuser


def user_is_admin(request):
    return request.user.groups.filter(name="Админ").exists() or request.user.is_superuser


@login_required
def player_lobby(request):
    active_sessions = Session.objects.all().order_by("-id")
    return render(request, "player_lobby.html", {"active_sessions": active_sessions})


@login_required
def player_room(request, session_id):
    selected_session = get_object_or_404(Session, id=session_id)
    return render(request, "player.html", {"session": selected_session})


@login_required
def host(request):
    # Проверка прав доступа
    if not user_is_host(request):
        return redirect("player_lobby")

    # text

    # 1. СОЗДАНИЕ СЕССИИ (Если её еще нет)
    if not request.user.sessions.exists():
        if request.method == "POST":
            form = SessionForm(request.POST)
            if form.is_valid():
                new_session = form.save(commit=False)
                new_session.owner = request.user
                new_session.save()
            else:
                return
            return render(request, "host.html", {"has_session": True, "is_playing": request.user.sessions.all()[0].is_playing})
        else:
            form = SessionForm()
            return render(request, "host.html", {"form": form, "has_session": False, "is_playing": False})

    # ==============================================================
    # 2. СБОР ДАННЫХ ДЛЯ ПАНЕЛИ (Медиатека, Плейлист, Сообщения)
    # ==============================================================

    # Медиатека
    my_audio = Audio.objects.filter(owner=request.user).order_by("-id")
    my_video = Video.objects.filter(owner=request.user).order_by("-id")

    # Плейлист и Shuffle
    playlist = Playlist.objects.filter(owner=request.user, title="Очередь эфира").first()
    playlist_elements = list(playlist.elements.all()) if playlist else []
    current_session = request.user.sessions.first()

    if current_session and current_session.is_shuffled:
        shuffled_ids = request.session.get("shuffled_ids", [])
        if shuffled_ids:
            playlist_elements.sort(key=lambda x: shuffled_ids.index(x.id) if x.id in shuffled_ids else 999)

    # === НОВОЕ: ВЫГРУЖАЕМ СООБЩЕНИЯ ОТ СЛУШАТЕЛЕЙ ===
    # Достаем сообщения, отправленные ИМЕННО ЭТОМУ ведущему (host=request.user)
    active_msgs = Message.objects.filter(host=request.user, state__in=["new", "in_progress"]).order_by("-creation_time")
    archived_msgs = Message.objects.filter(host=request.user, state="done").order_by("-creation_time")

    # 3. РЕНДЕР СТРАНИЦЫ
    return render(
        request,
        "host.html",
        {
            "form": None,
            "has_session": True,
            "is_playing": current_session.is_playing if current_session else False,
            "session": current_session,
            "my_video": my_video,
            "my_audio": my_audio,
            "playlist_elements": playlist_elements,
            # === НОВОЕ: ПЕРЕДАЕМ СООБЩЕНИЯ В HTML ===
            "active_msgs": active_msgs,
            "archived_msgs": archived_msgs,
        },
    )


@login_required
def upload_media(request):
    if request.method == "POST" and user_is_host(request):
        file = request.FILES.get("media_file")
        name = request.POST.get("name", "Без названия")
        file_type = request.POST.get("file_type")

        # text

        if file:
            try:
                if file_type == "audio":
                    new_media = Audio(owner=request.user, name=name, audio_file=file)
                elif file_type == "video":
                    new_media = Video(owner=request.user, name=name, video_file=file)
                new_media.full_clean()
                new_media.save()
                messages.success(request, f"Файл '{name}' успешно загружен!")
            except ValidationError as e:
                for field, error_list in e.message_dict.items():
                    for error in error_list:
                        messages.error(request, f"Ошибка загрузки: {error}")

        return redirect("host")
    return redirect("player_lobby")


@login_required
def player(request):
    return render(request, template_name="player.html")


def register(request):
    # text

    if request.user.is_authenticated:
        return redirect("player_lobby")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            listener, created = Group.objects.get_or_create(name="Слушатель")
            user.groups.add(listener)
            return redirect_if_user_wasnt_auth(request, user)
    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    # text

    if request.user.is_authenticated:
        return redirect("player_lobby")

    if request.method == "POST":
        form = CustomLoginForm(request.POST, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            return redirect_if_user_wasnt_auth(request, user)
    else:
        form = CustomLoginForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return redirect("player_lobby")


def redirect_if_user_wasnt_auth(request, user):
    login(request, user)
    next_url = request.POST.get("next") or request.GET.get("next")

    # text

    if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    else:
        return redirect("player_lobby")


@login_required
def add_to_playlist(request, item_id):
    if not user_is_host(request):
        return redirect("player_lobby")

    if request.method == "POST":
        item = get_object_or_404(MediatekElement, id=item_id, owner=request.user)

        # text

        playlist, created = Playlist.objects.get_or_create(owner=request.user, title="Очередь эфира")
        playlist.elements.add(item)

    return redirect("host")


@login_required
def remove_from_playlist(request, item_id):
    if not user_is_host(request):
        return redirect("player_lobby")

    if request.method == "POST":
        item = get_object_or_404(MediatekElement, id=item_id, owner=request.user)
        playlist = Playlist.objects.filter(owner=request.user, title="Очередь эфира").first()

        # text

        if playlist:
            playlist.elements.remove(item)

    return redirect("host")


@login_required
def toggle_shuffle(request):
    if request.method == "POST":
        session = request.user.sessions.first()
        if session:
            # Переключаем кнопку
            session.is_shuffled = not session.is_shuffled
            session.save()

            # text

            if session.is_shuffled:
                # Включили Shuffle: берем треки, перемешиваем их ID и запоминаем!
                playlist = Playlist.objects.filter(owner=request.user, title="Очередь эфира").first()
                if playlist:
                    # Достаем список ID (например: [1, 2, 3])
                    ids = list(playlist.elements.values_list("id", flat=True))
                    random.shuffle(ids)  # Перемешиваем: [3, 1, 2]

                    # Сохраняем в память (куки сервера)
                    request.session["shuffled_ids"] = ids
            else:
                # Выключили Shuffle: удаляем память
                if "shuffled_ids" in request.session:
                    del request.session["shuffled_ids"]

    return redirect("host")


@login_required
def toggle_loop(request):
    if request.method == "POST":
        session = request.user.sessions.first()
        if session:
            session.is_looping = not session.is_looping
            session.save()
    return redirect("host")


@login_required
def delete_media(request, media_type, media_id):
    # Разрешаем удалять только через POST-запрос (для безопасности)
    if request.method == "POST":

        # text

        # Определяем, в какой таблице искать
        if media_type == "audio":
            # Находим файл, причем ТОЛЬКО если он принадлежит текущему ведущему!
            media_item = get_object_or_404(Audio, id=media_id, owner=request.user)
            # Физически удаляем файл с диска
            if media_item.audio_file:
                media_item.audio_file.delete(save=False)

        elif media_type == "video":
            media_item = get_object_or_404(Video, id=media_id, owner=request.user)
            if media_item.video_file:
                media_item.video_file.delete(save=False)
        else:
            return redirect("host")

        # Удаляем запись из базы данных (при этом трек автоматически исчезнет и из плейлиста, если он там был)
        name = media_item.name
        media_item.delete()

        messages.success(request, f"Файл '{name}' успешно удален из медиатеки.")

    return redirect("host")


@csrf_exempt  # Отключаем CSRF, так как шлем из JS (для хакатона это безопасно)
@login_required
def upload_voice_message(request):
    if request.method == "POST":
        voice_file = request.FILES.get("voice_blob")
        action_type = request.POST.get("action_type")  # Получаем команду: 'live' или 'playlist'

        # text

        if voice_file:
            # 1. Сохраняем голосовое как обычный аудиофайл в медиатеку
            time_now = timezone.now().strftime("%H:%M:%S")
            audio_obj = Audio.objects.create(owner=request.user, name=f"🎙️ Голос ведущего ({time_now})", audio_file=voice_file)

            # 2. Обработка действий
            if action_type == "playlist":
                # ПРОСТО В ПЛЕЙЛИСТ
                playlist, _ = Playlist.objects.get_or_create(owner=request.user, title="Очередь эфира")
                playlist.elements.add(audio_obj)

            elif action_type == "live":
                # СРАЗУ В ЭФИР (Микширование)
                channel_layer = get_channel_layer()
                # Берем первую сессию юзера, чтобы узнать в какую комнату слать
                session = request.user.sessions.first()
                if session:
                    room_name = f"stream_{session.id}"
                    async_to_sync(channel_layer.group_send)(
                        room_name,
                        {
                            "type": "broadcast",  # Вызовет функцию broadcast в consumers.py
                            "event": "play_host_voice",
                            "url": audio_obj.audio_file.url,  # Передаем URL файла
                        },
                    )
            return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "bad request"}, status=400)


@login_required
def send_message(request):
    if request.method == "POST":
        session = Session.objects.filter(is_playing=True).first()
        if not session:
            session = Session.objects.first()

        # text

        if not session:
            messages.error(request, "Нет активных ведущих.")
            return redirect(request.META.get("HTTP_REFERER", "player_lobby"))

        host_user = session.owner
        new_msg = None
        text_content = request.POST.get("text", "")  # Берем пустую строку, если нет текста
        voice_file = request.FILES.get("voice_message")

        # 1. СОХРАНЯЕМ В БД
        if text_content:
            new_msg = TextMessage.objects.create(sender=request.user, host=host_user, text=text_content, creation_time=timezone.now(), state="new")
            messages.success(request, "Текст отправлен!")

        elif voice_file:
            new_msg = VoiceMessage.objects.create(
                sender=request.user, host=host_user, voice_message=voice_file, creation_time=timezone.now(), state="new"
            )
            messages.success(request, "Голос отправлен!")

        # ========================================================
        # 2. ИСПРАВЛЕННЫЙ WEBSOCKET (МАКСИМАЛЬНО БЕЗОПАСНЫЙ СЛОВАРЬ)
        # ========================================================
        if new_msg:
            # Если это текст, берем текст, если голос - берем пустую строку
            safe_text = str(text_content) if text_content else ""

            # Если это голос, берем его URL, если текст - пустую строку
            safe_voice_url = new_msg.voice_message.url if voice_file else ""

            channel_layer = get_channel_layer()
            room_name = f"stream_{session.id}"

            # Передаем ТОЛЬКО примитивные типы (int, str)
            async_to_sync(channel_layer.group_send)(
                room_name,
                {
                    "type": "broadcast",  # Вызовет broadcast в consumers.py
                    "event": "new_message",
                    "msg_id": int(new_msg.id),
                    "sender": str(request.user.username),
                    "text": safe_text,
                    "voice_url": safe_voice_url,
                },
            )

    return redirect(request.META.get("HTTP_REFERER", "player_lobby"))


# 2. ВЕДУЩИЙ МЕНЯЕТ СТАТУС
@login_required
def change_msg_status(request, msg_id):
    if request.method == "POST":
        msg = get_object_or_404(Message, id=msg_id, host=request.user)
        new_status = request.POST.get("status")

        # text

        # Если статус правильный - меняем
        if new_status in dict(Message.STATUS_CHOICES).keys():
            msg.state = new_status
            msg.save()

    return redirect("host")


@login_required
def delete_session(request):
    if request.method == "POST":
        # Находим первую сессию текущего пользователя (или можно использовать ID, если сессий несколько)
        session = Session.objects.filter(owner=request.user).first()
        if session:
            # Опционально: можно перед удалением разослать слушателям по WebSocket сигнал "Эфир завершен"
            # Но для простоты сейчас просто удаляем сессию из БД
            session.delete()
            messages.success(request, "Эфир успешно завершен и удален.")

    # text

    # Возвращаем ведущего обратно в его панель (там появится форма создания нового эфира)
    return redirect("host")


def is_admin(u):
    return u.groups.filter(name="Админ").exists() or u.is_superuser


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    context = {
        "total_users": User.objects.filter(is_deleted=False).count(),
        "active_users": User.objects.filter(is_deleted=False, is_active=True).count(),
        "listeners": User.objects.filter(groups__name="Слушатель").count(),
        "hosts": User.objects.filter(groups__name="Ведущий").count(),
    }
    return render(request, "admin/dashboard.html", context=context)


@login_required
@user_passes_test(is_admin)
def user_management(request):
    users = User.objects.filter(is_deleted=False).order_by("-date_joined")
    filter_form = UserFilterForm(request.GET)

    if filter_form.is_valid():
        login_query = filter_form.cleaned_data.get("login")
        if login_query:
            users = users.filter(username__icontains=login_query)
        full_name_query = filter_form.cleaned_data.get("full_name")
        if full_name_query:
            users = users.filter(fullName__icontains=full_name_query)
        role = filter_form.cleaned_data.get("role")
        if role:
            users = users.filter(groups__name=role)
        date_from = filter_form.cleaned_data.get("date_from")
        if date_from:
            users = users.filter(date_joined__gte=date_from)
        date_to = filter_form.cleaned_data.get("date_to")
        if date_to:
            date_to += datetime.timedelta(days=1)
            users = users.filter(date_joined__lt=date_to)

    context = {
        "users": users,
        "filter_form": filter_form,
    }
    return render(request, "admin/user_management.html", context)


@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Пользователь {user.username} успешно обновлен.")
            return redirect("users")
    else:
        form = UserEditForm(instance=user)
    return render(request, "admin/modals/edit_user.html", {"form": form, "user": user})


@login_required
@user_passes_test(is_admin)
def change_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserAdminPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, f"Пароль для {user.username} успешно изменен.")
            return redirect("users")
    else:
        form = UserAdminPasswordChangeForm(user)
    return render(request, "admin/modals/change_password.html", {"form": form, "user": user})


@login_required
@user_passes_test(is_admin)
def assign_roles(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserRoleAssignmentForm(request.POST)
        if form.is_valid():
            selected_roles = form.cleaned_data["roles"]
            user.groups.set(selected_roles)
            messages.success(request, f"Роли для {user.username} обновлены.")
            return redirect("users")
    else:
        initial_roles = user.groups.all()
        form = UserRoleAssignmentForm(initial={"roles": initial_roles})
    return render(request, "admin/modals/assign_roles.html", {"form": form, "user": user})


@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserDeleteForm(request.POST)
        if form.is_valid() and form.cleaned_data["confirm"]:
            user.is_deleted = True
            user.save()
            messages.success(request, f"Пользователь {user.username} помечен как удаленный.")
            return redirect("users")
    else:
        form = UserDeleteForm()
    return render(request, "admin/modals/delete_user.html", {"form": form, "user": user})
