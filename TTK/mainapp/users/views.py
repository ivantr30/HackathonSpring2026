from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
import logging

from .forms import (
    RegistrationForm,
    LoginForm,
)
from .models import User, UserActivity

# from .utils import get_client_ip, log_user_activity

logger = logging.getLogger(__name__)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    login(request, user)

                    messages.success(request, f"Добро пожаловать, {user.username}!")
                    return redirect("users:dashboard")
            except Exception as e:
                logger.error(f"Registration error: {e}")
                messages.error(request, "Ошибка регистрации. Попробуйте позже.")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegistrationForm()

    context = {
        "form": form,
        "title": "Регистрация",
        "year": timezone.now().year,
    }
    return render(request, "users/auth/register.html", context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            remember_me = form.cleaned_data.get("remember_me", False)

            user = None
            if "@" in username:
                try:
                    user_obj = User.objects.get(email=username)
                    username = user_obj.username
                except User.DoesNotExist:
                    pass

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)

                messages.success(request, f"С возвращением, {user.username}!")
                next_url = request.GET.get("next", "users:dashboard")
                return redirect(next_url)
            else:
                messages.error(request, "Неверный логин или пароль")
    else:
        form = LoginForm()

    context = {
        "form": form,
        "title": "Вход",
        "year": timezone.now().year,
    }
    return render(request, "users/auth/login.html", context)


@login_required
def logout_view(request):
    try:
        logout(request)
        messages.info(request, "Вы вышли из системы")
    except Exception as e:
        logger.error(f"Logout error: {e}")
    return redirect("users:login")
