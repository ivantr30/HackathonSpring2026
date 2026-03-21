from django.shortcuts import render, redirect
from .forms import RegistrationForm, SessionForm, CustomLoginForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group 

# Create your views here.
@login_required
def player(request):
    return render(request, 'player.html')
@login_required
def host(request):
    if request.user.groups.filter(name="Ведущий").exists() or request.user.is_superuser:
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
        else:
            return render(request, 'host.html', {"has_session" : True, "is_playing" : request.user.sessions.all()[0].is_playing})
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
    
