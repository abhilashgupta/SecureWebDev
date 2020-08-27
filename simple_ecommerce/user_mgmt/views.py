from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.models import User
import datetime
from django import forms
from django.http import HttpResponse

def index(request):
    return render(request, 'index.html')

def registration(request):
    if request.method == 'POST':
        f = RegistrationForm(request.POST)
        # print(f)
        if f.is_valid():
            username = f.cleaned_data.get('username')
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, 'Username already registered. Please use a new username.')
                return redirect ('registration')
            password = f.cleaned_data.get('password1')
            last_name = f.cleaned_data.get('last_name')
            first_name = f.cleaned_data.get('first_name')
            new_user = User.objects.create(username=username, 
                    last_name=last_name, first_name=first_name)
            new_user.set_password(password)
            new_user.save()
            messages.success(request, 'Account created successfully. Your account \
                activation details has been sent to your email address. Please \
                    activate your account to log in.')
            return redirect('registration')
        elif f.errors:
            for v in f.errors.values():
                messages.error(request, v)
            # print(f.errors)
            return render(request, 'registration.html', {'form': f})
        else:
            messages.error(request, 'Account creation failed')
            # print(f)
            return render(request, 'registration.html', {'form': f})

    else:
        f = RegistrationForm()
    return render(request, 'registration.html', {'form': f})

def activation(request, username, token_slug):
    if User.objects.filter(username__iexact=username).exists():
        user = User.objects.get(username=username)
        if user.useractivationinfo.enabled :
            response = '{}\'s user account is already activated. Please login at <a href="../../login">login page</a>'
            return HttpResponse(response.format(username))
        elif user.useractivationinfo.activation_token != token_slug :
            response = "User account {}'s activation token doesn't match with {}.<br>\
                        Please inform correct token"
            return HttpResponse(response.format(username, token_slug) )
        else :
            user.useractivationinfo.enabled = True
            user.useractivationinfo.save()
            user.date_joined = datetime.datetime.now()
            user.save()
            return render(request, 'activated.html', {'username': username})
    else:
        response = "User account {} doesn't exist. Please register first at \
                    <a href='../../registration'>registration page</a>."
        return HttpResponse(response.format(username))