from django.shortcuts import render, redirect, get_object_or_404
from .forms import (
    RegistrationForm,
    UserFilterForm,
    UserEditForm,
    UserAdminPasswordChangeForm,
    UserRoleAssignmentForm,
    UserDeleteForm,
)
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group
from django.contrib import messages
import datetime

User = get_user_model()


@login_required
def player(request):
    return render(request, template_name="player.html")


def register(request):

    if request.user.is_authenticated:
        return redirect("player")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            listener = Group.objects.get_or_create(name="Слушатель")
            user.groups.add(listener)
            return redirect_if_user_wasnt_auth(request, user)
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})


def login_view(request):

    if request.user.is_authenticated:
        return redirect("player")

    if request.method == "POST":
        form = AuthenticationForm(request.POST, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            return redirect_if_user_wasnt_auth(request, user)
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return player(request)


def redirect_if_user_wasnt_auth(request, user):
    login(request, user)
    next_url = request.POST.get("next") or request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    else:
        return redirect("player")


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
