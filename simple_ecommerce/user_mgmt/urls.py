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
    # path('accounts/password-reset', auth_views.PasswordResetView.as_view(template_name="password_reset_form.html"), name='password_reset'),
    # path('accounts/password-reset/done', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
]