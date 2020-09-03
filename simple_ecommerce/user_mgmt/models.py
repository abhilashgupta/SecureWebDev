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
    salt = models.CharField(max_length=32, default=secrets.token_urlsafe(32))


class Product(models.Model):
    pkey = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(max_length=100) #use this in the urls.
    price = models.DecimalField(max_digits=11, decimal_places=2, 
                    validators=[MinValueValidator(0.01, 
                        "Value of price can't be less than 0,01.")])
    # pr = models.DecimalField()
    special_price = models.DecimalField(max_digits=11, decimal_places=2, 
                    validators=[MinValueValidator(0.01, 
                        "Value of special price can't be less than 0,01.")])
    count = models.IntegerField(validators=[MinValueValidator(0, "Value of count can't be less than 0.")])
    image = models.URLField()
    seller = models.UUIDField() # this will map to uuid of partner or self where
    # self = uuid.UUID(int=0x0)

class CartItem(models.Model):
    pk = models.AutoField(primary_key=True)
    product_id = models.UUIDField() #uid of product
    quantity = models.IntegerField(validators=[MinValueValidator(0, "Value of quantity can't be less than 0.")])
    order_id = models.IntegerField(validators=[MinValueValidator(0, "Value of order_id can't be less than 0.")])

class Payment(models.Model):
    pk = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=11, decimal_places=2, 
                    validators=[MinValueValidator(0.01, 
                        "Value of price can't be less than 0,01.")])
    method = models.CharField(max_length=100)

class Address(models.Model):
    pk = models.AutoField(primary_key=True)
    user = models.CharField(max_length=150) #username(email in our case) of user
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.IntegerField()
    country = models.CharField(max_length=100)
    additional_info = models.TextField()

class Order(models.Model):
    pk = models.AutoField(primary_key=True)
    customer_id = models.CharField(max_length=150)
    placed = models.BooleanField(default=False)
    date_placed = models.DateField()
    shipping_address = models.IntegerField() #pk of address object
    payment = models.IntegerField() #pk of payment object