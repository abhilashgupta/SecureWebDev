from django.forms import ModelForm
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
# from registration.forms import RegistrationFormUniqueEmai
# , RegistrationFormUniqueEmail
from django import forms

class RegistrationForm(UserCreationForm):
    username = forms.EmailField(help_text='Required. Inform a valid email id only. \
                                        This will be your username',)
    first_name = forms.CharField(max_length=150, help_text="Inform your middle name, if any, here.",)
    last_name = forms.CharField (max_length=150)

    # def clean_username(self):
    #     username = self.cleaned_data.get('username')
    #     if User.objects.filter(username__iexact=username).exists():
    #         raise forms.ValidationError('Username already exists')
    #     return username
    
    
    class Meta:
        model = User
        fields = ["first_name", "last_name", "password1", "password2"]