from django.urls import path

from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    # path('index/', views.index, name='index'),
    path('accounts/registration', views.registration, name='registration'),
    path('accounts/<username>/verify/<slug:token_slug>', views.activation, name='activation'),
    # path('accounts/login', views.login, name='login'),
]