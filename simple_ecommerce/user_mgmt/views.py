from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.models import User
import datetime, secrets
from django import forms
from django.http import HttpResponse, Http404
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

def index(request):
    return render(request, 'index.html')

def registration(request):
    if request.method == 'POST':
        f = RegistrationForm(request.POST)
        # print(f)
        if f.is_valid():
            username = f.cleaned_data.get('username')
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, 'Username already exists. Please use a new username.')
                return redirect ('registration')
            last_name = f.cleaned_data.get('last_name')
            first_name = f.cleaned_data.get('first_name')
            password = f.clean_password2()
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

Subject =  "Password reset on thin-air"
From = "do-not-reply@thin-air.com"
Message = "Dear {}, \n\
You're receiving this email because you requested a password reset for your user account at thin-air. \n\
Please go to the following page within an hour and choose a new password: \n\
http://{}/accounts/reset/{}/{} \n\
Your username is your email id. \n\
Thanks for using our site! \n\
The thin-air team"


def password_reset_request(request):
    if request.method == 'POST':
        f = PasswordResetForm(request.POST)
        # print(f)
        if f.is_valid():
            username = f.cleaned_data.get('email')
            if User.objects.filter(username__iexact=username).exists():
                user = User.objects.get(username=username)
                reset_time = datetime.datetime.now() + datetime.timedelta(hours=1)
                token = secrets.token_urlsafe(64)
                user.useractivationinfo.reset_token = token
                user.useractivationinfo.reset_time = reset_time
                user.useractivationinfo.save()
                msg = Message.format(user.username, request.get_host(), 
                            user.username, user.useractivationinfo.reset_token)
                send_mail(Subject, msg, From, [user.username])
                return redirect("password_reset_request_done")
            else :
                messages.error(request, "No such account exists.")
                return render(request, 'password_reset_request.html', {'form': f})
        else :
            return render(request, 'password_reset_request.html', {'form': f})
    else:
        f = PasswordResetForm()
    return render(request, 'password_reset_request.html', {'form': f})

def password_reset_request_done(request):
    return render(request, 'password_reset_request_done.html')

def new_password_authentication(request, username, token_slug):
    user = get_object_or_404(User, username=username)
    if token_slug == user.useractivationinfo.reset_token and \
                datetime.datetime.now(datetime.timezone.utc) < user.useractivationinfo.reset_time :
        f = SetPasswordForm(user)
        return render(request, 'new_password_authentication.html', {'form': f, 'username':username})
    else :
        now = datetime.datetime.now(datetime.timezone.utc)
        # print (now)
        # print (user.useractivationinfo.reset_time)
        if now < user.useractivationinfo.reset_time:
            user.useractivationinfo.reset_time = datetime.datetime.now()
            user.useractivationinfo.save()
        return HttpResponse(request, 'Invalid Token.')

def new_password_confirmation(request, username):
    print ('new_password_confirmation called.')
    if request.method == 'POST':
        user = get_object_or_404(User, username=username)
        f = SetPasswordForm(user, request.POST)
        print ("f=\n", f )
        if f.errors:
            print ("case errors")
            for v in f.errors.values():
                messages.error(request, v)
        else:
            print("f.is_valid=", f.is_valid())
            print("f.errors:", f.errors)
            
            if datetime.datetime.now(datetime.timezone.utc) < user.useractivationinfo.reset_time: 
                password = f.clean_new_password2()
                user.set_password(password)
                user.save()
                user.useractivationinfo.reset_time = datetime.datetime.now()
                user.useractivationinfo.save()
                messages.success(request, "Password change successful. Please login with your new password.")
                return render(request, 'post_password_change_attempt.html')
            else:
                messages.error(request, "Invalid Attempt.")
                return render(request, 'post_password_change_attempt.html')
    else:
        print ("abcd")
        messages.error(request, "Invalid Attempt.")
        return render(request, 'post_password_change_attempt.html')