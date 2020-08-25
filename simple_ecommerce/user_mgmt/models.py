import datetime

from django.db import models
from django.utils import timezone

# Create your models here.

class User(models.Model):
    username = models.EmailField() #default max_length = 254
    password = models.CharField(max_length=256) # Charfield for now, update if required (also length)
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    datetime joined = models.DateTimeField('Time and Date joined') #Needs autoupdate when a user joins
    enabled = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=256) # Charfield for now, update if required (also length). Also needs autoupdate.

    def __str__(self):
        return self.first_name + " " + self.last_name
