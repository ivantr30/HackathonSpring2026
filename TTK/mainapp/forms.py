import re
from .models import User, Session
from django.contrib.auth.forms import AdminPasswordChangeForm, UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth.models import Group


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "fullName"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Ваш логин"}),
            "fullName": forms.TextInput(attrs={"placeholder": "Ваше ФИО"}),
            "password1": forms.TextInput(attrs={"placeholder": "Ваш пароль"}),
            "password2": forms.TextInput(attrs={"placeholder": "Подтверджение пароля"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Ваш пароль",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Подтверждение пароля",
            }
        )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and not re.match(r"^[a-zA-Z]+$", username):
            raise forms.ValidationError("Логин должен содержать только латинские буквы.")
        return username

    def clean_fullName(self):
        full_name = self.cleaned_data.get("fullName")
        if full_name and not re.match(r"^[А-Яа-яЁё\s-]+$", full_name):
            raise forms.ValidationError("ФИО может содержать только русские буквы, пробелы и дефис.")
        return full_name

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password1")

        if password and not re.match(r"^[\x20-\x7E]+$", password):
            self.add_error("password1", "Пароль может содержать только латинские буквы, цифры и спецсимволы.")
        return cleaned_data


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "session-title", "placeholder": "Введите название эфира"}),
        }


class CustomLoginForm(AuthenticationForm):
    # Способ с переопределением полей (самый красивый для обычных форм)
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={"placeholder": "Ваш логин", "class": "my-input"}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"placeholder": "Ваш пароль", "class": "my-input"}))


class UserFilterForm(forms.Form):
    login = forms.CharField(label="Логин", required=False, widget=forms.TextInput(attrs={"placeholder": "Поиск по логину"}))
    full_name = forms.CharField(label="ФИО", required=False, widget=forms.TextInput(attrs={"placeholder": "Поиск по ФИО"}))
    role = forms.ChoiceField(
        label="Роль",
        required=False,
        choices=[("", "Все")] + [(g.name, g.name) for g in Group.objects.filter(name__in=["Слушатель", "Ведущий", "Админ"])],
        widget=forms.Select(attrs={"class": "role-select"}),
    )
    date_from = forms.DateField(label="Дата регистрации от", required=False, widget=forms.DateInput(attrs={"type": "date", "class": "date-input"}))
    date_to = forms.DateField(label="Дата регистрации до", required=False, widget=forms.DateInput(attrs={"type": "date", "class": "date-input"}))


class UserEditForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.filter(name__in=["Слушатель", "Ведущий", "Админ"]), widget=forms.CheckboxSelectMultiple, required=False, label="Группы"
    )

    class Meta:
        model = User
        fields = ["username", "fullName", "is_active", "groups"]
        labels = {
            "username": "Логин",
            "fullName": "ФИО",
            "is_active": "Активен",
        }


class UserAdminPasswordChangeForm(AdminPasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["password1"].label = "Новый пароль"
        self.fields["password2"].label = "Подтверждение пароля"


class UserRoleAssignmentForm(forms.Form):
    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.filter(name__in=["Слушатель", "Ведущий", "Админ"]), widget=forms.CheckboxSelectMultiple, label="Роли"
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        super().__init__(*args, **kwargs)
        if "roles" in initial:
            self.fields["roles"].initial = initial["roles"]


class UserDeleteForm(forms.Form):
    confirm = forms.BooleanField(label="Подтверждаю удаление", required=True)
