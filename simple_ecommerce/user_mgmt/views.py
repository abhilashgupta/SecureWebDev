from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.models import User
import datetime
from django import forms
from django.http import HttpResponse, Http404

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
            return render(request, 'index.html')
            # response = '{}\'s user account is already activated. Please login at <a href="../../login">login page</a>'
            # return HttpResponse(response.format(username))
        elif user.useractivationinfo.activation_token != token_slug :
            raise Http404("This is not the page that you are looking for!")
        else :
            user.useractivationinfo.enabled = True
            user.useractivationinfo.save()
            user.date_joined = datetime.datetime.now()
            user.save()
            return render(request, 'activated.html', {'username': username})
    else:
        raise Http404("This is not the page that you are looking for!")

# def password_reset(request, username):
#     if User.objects.filter(username__iexact=username).exists():
#         user = User.objects.get(username=username)