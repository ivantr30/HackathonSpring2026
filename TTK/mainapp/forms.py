import re
from .models import User, Session
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "fullName"]
        widgets = {
            "username" : forms.TextInput(attrs={"placeholder" : "Ваш логин"}),
            "fullName" : forms.TextInput(attrs={"placeholder" : "Ваше ФИО"}),
            "password1" : forms.TextInput(attrs={"placeholder" : "Ваш пароль"}),
            "password2" : forms.TextInput(attrs={"placeholder" : "Подтверджение пароля"}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Ваш пароль',
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Подтверждение пароля',
        })
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and not re.match(r'^[a-zA-Z]+$', username):
            raise forms.ValidationError("Логин должен содержать только латинские буквы.")
        return username

    def clean_fullName(self):
        full_name = self.cleaned_data.get("fullName")
        if full_name and not re.match(r'^[А-Яа-яЁё\s-]+$', full_name):
            raise forms.ValidationError("ФИО может содержать только русские буквы, пробелы и дефис.")
        return full_name

    def clean(self):
        cleaned_data = super().clean()
        
        password = cleaned_data.get("password1")
        
        if password:
            if not re.match(r'^[\x20-\x7E]+$', password):
                self.add_error('password1', "Пароль может содержать только латинские буквы, цифры и спецсимволы.")
                
        return cleaned_data
class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['title']
        widgets = {
            'title' : forms.TextInput(attrs={"class" : "session-title", "placeholder" : "Введите название эфира"}),
        }
class CustomLoginForm(AuthenticationForm):
    # Способ с переопределением полей (самый красивый для обычных форм)
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={"placeholder": "Ваш логин", "class": "my-input"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Ваш пароль", "class": "my-input"})
    )