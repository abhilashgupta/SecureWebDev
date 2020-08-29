from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    # path('index/', views.index, name='index'),
    path('accounts/registration', views.registration, name='registration'),
    path('accounts/<username>/verify/<slug:token_slug>', views.activation, name='activation'),
    path('accounts/login', auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('accounts/logout', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('index', views.index, name='index'),
    path('accounts/password-reset', views.password_reset_request, name='password_reset_request'),
    path('accounts/password-reset/done', views.password_reset_request_done, name='password_reset_request_done'),
    path('accounts/reset/<username>/confirm', views.new_password_confirmation, name='new_password_confirmation'),
    path('accounts/reset/<username>/<slug:token_slug>', views.new_password_authentication, name='new_password_authentication'),
]