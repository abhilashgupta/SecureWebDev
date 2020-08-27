import datetime
import string
import random

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
# Create your models here.

# No changes made to the existing User model (with unique and compulsory username
# but non required email). There I will just enforce username to be email. That 
# is the plan for now. Hopefully it will work.
class UserActivationInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=100)

# Example modified from https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
# Maybe move this to a handler. Let's see.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserActivationInfo.objects.create(user=instance)
        letters_digits = string.ascii_letters + string.digits
        random_char_list = random.choices(letters_digits, k=64)
        random_char_string = ''.join(random_char_list) # random string of length 64
        instance.useractivationinfo.activation_token = random_char_string
        activation_url = "127.0.0.1:8000/accounts/"+ instance.username + "/verify/" + random_char_string
        print ("Activation link:", activation_url)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.useractivationinfo.save()