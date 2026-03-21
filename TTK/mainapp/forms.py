import re
from .models import User
from django.contrib.auth.forms import UserCreationForm, AdminPasswordChangeForm
from django import forms
from django.contrib.auth.models import Group


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "fullName"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password1")
        if password and not re.match(r"^[\x20-\x7E]+$", password):
            self.add_error("password1", "Пароль может содержать только латинские буквы, цифры и символы.")
        return cleaned_data


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
