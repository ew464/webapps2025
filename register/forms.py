from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    currency = forms.ChoiceField(choices=User.CURRENCY_CHOICES)

    class Meta:
        model = User
        exclude = ['role']
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'currency']

