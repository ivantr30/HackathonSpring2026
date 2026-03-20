from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import Group 

# Create your views here.
@login_required 
def player(request):
    return render(request, template_name='player.html')
def register(request):

    if request.user.is_authenticated:
        return redirect('player')
    
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            listener = Group.objects.get_or_create(name="Слушатель")
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