import re
from .models import User, Session
from django.contrib.auth.forms import UserCreationForm
from django import forms

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "fullName"]
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password1")
        if password:
            if not re.match(r'^[\x20-\x7E]+$', password):
                self.add_error('password1', "Пароль может содержать только латинские буквы, цифры и символы.")
                
        return cleaned_data
class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["title"]