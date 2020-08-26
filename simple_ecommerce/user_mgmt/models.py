import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# Create your models here.

# No changes made to the existing User model (with unique and compulsory username
# but non required email). There I will just enforce username to be email. That 
# is the plan for now. Hopefully it will work.
class UserActivationInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=100)
