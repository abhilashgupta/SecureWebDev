import datetime
import string
import random

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
import secrets, uuid
from django.core.validators import MinValueValidator

# No changes made to the existing User model (with unique and compulsory username
# but non required email). There I will just enforce username to be email.ß
class UserActivationInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=100)
    reset_token = models.CharField(max_length=100, default="")
    reset_time = models.DateTimeField(default=timezone.now) #only until this time, is the reset token valid.

# Example modified from https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserActivationInfo.objects.create(user=instance)
        random_token = secrets.token_urlsafe(64)
        instance.useractivationinfo.activation_token = random_token
        instance.useractivationinfo.reset_token = ""
        instance.useractivationinfo.reset_time = datetime.datetime.now()
        activation_url = "127.0.0.1:8000/accounts/"+ instance.username + "/verify/" + random_token
        print ("Activation link:", activation_url)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.useractivationinfo.save()

class Partner(models.Model):
    pkey = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    website = models.URLField()
    token = models.CharField(max_length=100)


class Product(models.Model):
    pkey = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(max_length=100) #use this in the urls.
    price = models.DecimalField(max_digits=11, decimal_places=2)
    special_price = models.DecimalField(max_digits=11, decimal_places=2)
    abc = models.IntegerField()
    count = models.IntegerField(validators=[MinValueValidator(0, "Value of count can't be less than 0.")])
    image = models.URLField()
    seller = models.CharField(max_length=100)