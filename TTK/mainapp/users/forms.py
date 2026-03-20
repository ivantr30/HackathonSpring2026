import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import User, UserSettings


class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        label="ФИО", max_length=150, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Иванов Иван Иванович"})
    )
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "example@mail.com"}))
    username = forms.CharField(
        label="Логин", min_length=3, max_length=30, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "username"})
    )
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "********"}))
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "********"}))

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "password1", "password2"]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not re.match(r"^[a-zA-Z]+$", username):
            raise ValidationError("Логин может содержать только латинские буквы (a-z, A-Z)")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким логином уже существует")
        return username

    def clean_full_name(self):
        full_name = self.cleaned_data.get("full_name")
        if not re.match(r"^[а-яА-ЯёЁ\s\-]+$", full_name):
            raise ValidationError("ФИО может содержать только русские буквы, пробелы и дефис")
        return full_name

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if len(password) < 8:
            raise ValidationError("Пароль должен содержать не менее 8 символов")
        if not re.match(r"^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};:\\|,.<>/?]+$", password):
            raise ValidationError("Пароль может содержать только латинские буквы, цифры и спецсимволы")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"[0-9]", password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data["full_name"]
        user.email = self.cleaned_data["email"]
        user.role = User.UserRole.USER
        if commit:
            user.save()
            UserSettings.objects.get_or_create(user=user)
        return user


class LoginForm(forms.Form):
    username = forms.CharField(label="Логин или Email", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "username or email"}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "********"}))
    remember_me = forms.BooleanField(label="Запомнить меня", required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
