from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from environs import Env


# example.env contains details needed for this. Not pushing my own client id.
# If that is needed, let me know and I will supply it for evaluation.
env = Env()
env.read_env()
gO2ClientId = env("GoogleOAuth2ClientID")

# I have used Django's django.contrib.auth.views for login and logout
# This has led to implementing a little complicated, possibly hacky, way to integrate
# Google SSO but it works.
extra_context = {'ClientId' : gO2ClientId}
urlpatterns = [
    path('accounts/registration', views.registration, name='registration'),
    path('accounts/<username>/verify/<slug:token_slug>', views.activation, name='activation'),
    path('accounts/google_login', views.google_login, name='google_login'),
    path('accounts/login', auth_views.LoginView.as_view(template_name="login.html", 
                                extra_context=extra_context), name='login'),
    path('accounts/logout', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('index', views.index, name='index'),
    path('accounts/password-reset', views.password_reset_request, name='password_reset_request'),
    path('accounts/password-reset/done', views.password_reset_request_done, name='password_reset_request_done'),
    path('accounts/reset/<username>/confirm', views.new_password_confirmation, name='new_password_confirmation'),
    path('accounts/reset/<username>/<slug:token_slug>', views.new_password_authentication, name='new_password_authentication'),
]