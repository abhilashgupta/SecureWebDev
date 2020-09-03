from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.models import User
import datetime, secrets, json, time, random, uuid, string
from django import forms
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseBadRequest
from django.contrib.auth import login
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from google.oauth2 import id_token
from google.auth.transport import requests
from environs import Env
from hashlib import sha256
from .models import Partner, Product, CartItem, Payment, Address, Order
from django.core.serializers import serialize
from django.core.serializers.python import Serializer
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET, require_POST

def index(request):
    return render(request, 'index.html')

def registration(request):
    if request.method == 'POST':
        f = RegistrationForm(request.POST)
        if f.is_valid():
            username = f.cleaned_data.get('username')
            if User.objects.filter(username__exact=username).exists():
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
            return render(request, 'registration.html', {'form': f})
        else:
            messages.error(request, 'Account creation failed')
            return render(request, 'registration.html', {'form': f})
    else:
        f = RegistrationForm()
    return render(request, 'registration.html', {'form': f})

def activation(request, username, token_slug):
    if User.objects.filter(username__exact=username).exists():
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
        if f.is_valid():
            username = f.cleaned_data.get('email')
            if User.objects.filter(username__exact=username).exists():
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
        if now < user.useractivationinfo.reset_time:
            user.useractivationinfo.reset_time = datetime.datetime.now()
            user.useractivationinfo.save()
        return HttpResponse(request, 'Invalid Token.')

def new_password_confirmation(request, username):
    if request.method == 'POST':
        user = get_object_or_404(User, username=username)
        f = SetPasswordForm(user, request.POST)
        if f.errors:
            for v in f.errors.values():
                messages.error(request, v)
        else:
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
        messages.error(request, "Invalid Attempt.")
        return render(request, 'post_password_change_attempt.html')

def google_login(request):
    if request.method == 'POST':
        # This below part until try-except block is copied from https://stackoverflow.com/a/3244765
        # I doubt there is any other simple way to do it though.
        json_data = json.loads(request.body)
        try:
            token = json_data['token']
            redirect_to_shop = json_data['redirect_to_shop']
        except KeyError:
            return HttpResponseBadRequest("Malformed data!")

        # example.env contains details needed for this. Not pushing my own client id.
        # If that is needed, let me know and I will supply it for evaluation.
        env = Env()
        env.read_env()
        CLIENT_ID = env("GoogleOAuth2ClientID")

        try:
            # Raises ValueError when token can't be verified
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        except ValueError:
            return HttpResponseBadRequest("Invalid token!")

        username = idinfo.get('email')
        non_expired_token = time.time() <= idinfo['exp']
        username_verified = idinfo.get('email_verified')

        if username and username_verified and non_expired_token:
            if User.objects.filter(username__exact=username).exists():
                # we have a user who already has an account with this email
                user = User.objects.get(username=username)
                login(request, user)
                if redirect_to_shop == "false":
                    response = HttpResponse()
                    response['redirect_to_shop'] = "False"
                    return response
                else:
                    response = HttpResponse()
                    response['redirect_to_shop'] = redirect_to_shop
                    return response
            else:
                # we have a new user who is directly authenticating against SSO
                # using a random string as their password population since they
                # won't be using this and also won't be needing to regenerate a
                # password until the user revokes permission at google for thin-air.
                password = secrets.token_urlsafe(32)
                last_name = idinfo['family_name']
                first_name = idinfo['given_name']
                new_user = User.objects.create(username=username,
                        last_name=last_name, first_name=first_name)
                new_user.set_password(password)
                new_user.date_joined = datetime.datetime.now()
                new_user.save()
                new_user.useractivationinfo.enabled = True
                new_user.useractivationinfo.save()
                login(request, new_user)
                if redirect_to_shop == "false":
                    response = HttpResponse()
                    response['redirect_to_shop'] = "False"
                    return response
                else:
                    response = HttpResponse()
                    response['redirect_to_shop'] = redirect_to_shop
                    return response
        else:
            return HttpResponseBadRequest("Invalid token")
    else:
        raise Http404("This is not the page that you are looking for!")

# First I need a couple of dummy routines to populate the databases.

def add_dummy_partner():
    uid = uuid.uuid4()
    print ("your uid is:", uid)
    name_list = random.choices(string.ascii_lowercase, k=5)
    name = ''.join(name_list)
    print ("your name is:", name)
    url = "http://"+ name +".com"
    token = secrets.token_urlsafe(32)
    salt = secrets.token_urlsafe(32)
    print ("your token is: ", token)
    token_hash = sha256((token + salt).encode('utf-8')).hexdigest()
    print("the stored token hash is", token_hash)
    new_partner = Partner.objects.create(pkey=uid, name=name, website=url, 
                                        token=token_hash, salt=salt)
    new_partner.save()

desc_filler_text = '''Lorem ipsum dolor sit amet, consectetur adipiscing elit, 
                    sed do eiusmod tempor incididunt ut labore et 
                    dolore magna aliqua. Ut enim ad minim veniam, 
                    quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
                    Duis aute irure dolor in reprehenderit in voluptate 
                    velit esse cillum dolore eu fugiat nulla pariatur. 
                    Excepteur sint occaecat cupidatat non proident, sunt 
                    in culpa qui officia deserunt mollit anim id est laborum.'''

def add_dummy_product(sellerid=0):
    # pkey = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # name = models.CharField(max_length=100)
    # description = models.TextField()
    # slug = models.SlugField(max_length=100) #use this in the urls.
    # price = models.DecimalField(max_digits=11, decimal_places=2)
    # special_price = models.DecimalField(max_digits=11, decimal_places=2)
    # count = models.IntegerField(validators=[MinValueValidator(0, "Value of count can't be less than 0.")])
    # image = models.URLField()
    # seller = models.UUIDField()
    uid = uuid.uuid4()
    name_list = []
    for i in range(3):
        nl_member = ''.join(random.choices(string.ascii_lowercase, k=5))
        name_list.append(nl_member)
    name = ' '.join(name_list)
    description = desc_filler_text
    numlist = random.choices(string.digits, k=7)
    num = ''.join(numlist)
    name_list.append(num)
    slug = '-'.join(name_list)
    price = float(random.randint(1550, 3890))/100
    special_price = price - 10
    count = random.randint(0, 4)
    image = "http://localhost:3000/" + num + ".jpeg"
    if sellerid == 0:
        seller = uuid.UUID(int=0x0)
    else :
        seller = uuid.UUID(sellerid)
    print ("product details: ", name, slug, price, count, seller)
    new_product = Product.objects.create(pkey=uid, name=name, description=description, 
                                        slug=slug, price=price, special_price=special_price,
                                        count=count, image=image, seller=seller)

# The following code to implement the MySerialiser which excludes model and pkey 
# values has been taken from https://stackoverflow.com/a/5768757

class MySerialiser(Serializer):
    def end_object( self, obj ):
        self._current['id'] = obj._get_pk_val()
        self.objects.append(self._current)

def get_token_from_request(request):
    if 'HTTP_AUTHORIZATION' in request.META:
        bearer_token = request.META['HTTP_AUTHORIZATION']
        bearer_token = bearer_token.split(" ")
        if len(bearer_token) == 2 and bearer_token[0] == "Bearer":
            token = bearer_token[1]
            # print (bearer_token)
            # print (token)
            return token
        else:
            return None
    else:
        return None

@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def get_or_delete_product(request, p_id):
    if request.method == 'GET':
        # return product details if authorised
        valid_request = False
        token = get_token_from_request(request)
        if token is None:
            return HttpResponseBadRequest("Bad Request\n")
        if Product.objects.filter(slug__exact=p_id).exists():
            product = Product.objects.get(slug=p_id)
        else:
            return HttpResponseBadRequest("Bad Request\n")
        if product.seller == uuid.UUID(int=0x0):
            valid_request = True
        else:
            try:
                partner = Partner.objects.get(pkey=product.seller)
            except Partner.DoesNotExist:
                print("Partner not found!!")
                return HttpResponseBadRequest("Bad Request\n")
            print("Partner's name:", partner.name)
            if partner.token == sha256((token + partner.salt).encode('utf-8')).hexdigest():
                valid_request = True
                # print ("token recieved:", token)
        if valid_request:
            myserializer = MySerialiser()
            response = HttpResponse(myserializer.serialize(Product.objects.filter(slug__exact=p_id)))
            response['Cache-Control'] = "no-cache"
            return response
        else:
            return HttpResponseBadRequest("Bad Request\n")
    elif request.method == 'DELETE':
        # delete product details if authorised
        valid_request = False
        token = get_token_from_request(request)
        if token is None:
            return HttpResponseBadRequest("Bad Request\n")
        if Product.objects.filter(slug__exact=p_id).exists():
            product = Product.objects.get(slug=p_id)
        else:
            return HttpResponseBadRequest("Bad Request\n")
        try:
            partner = Partner.objects.get(pkey=product.seller)
        except Partner.DoesNotExist:
            print("Partner not found!!")
            return HttpResponseBadRequest("Bad Request\n")
        print("Partner's name:", partner.name)
        if partner.token == sha256((token + partner.salt).encode('utf-8')).hexdigest():
            product.delete()
            return HttpResponse("Product deleted successfully\n")
        else:
            return HttpResponseBadRequest("Bad Request\n")
    else:
        return HttpResponseBadRequest("Bad Request\n")

@csrf_exempt
@require_POST
def create_product(request):
    if request.method == 'POST':
        token = get_token_from_request(request)
        if token is None:
            return HttpResponseBadRequest("Bad Request\n")
        request_partner = None
        for partner in Partner.objects.all():
            if partner.token == sha256((token + partner.salt).encode('utf-8')).hexdigest():
                request_partner = partner
                break
        if request_partner is None:
            return HttpResponseBadRequest("Bad Request\n")
        uid = partner.pkey
        prod = request.POST
        # print(prod)
        uid = uuid.uuid4()
        slug = prod["name"].replace(" ", "-")
        numlist = random.choices(string.digits, k=7)
        num = ''.join(numlist)
        slug += "-"+num
        # print ("Slug: ", slug)
        new_product = Product.objects.create(pkey=uid, name=prod["name"], description=prod["description"], 
                                        slug=slug, price=prod["price"], special_price=prod["special_price"],
                                        count=prod["count"], image=prod["image"], seller=partner.pkey)
        new_product.save()
        return HttpResponse("Successfully saved product!\n")
    else:
        return HttpResponseBadRequest("Bad Request\n")

@require_GET
def get_products(request):
    if request.method == 'GET':
        token = get_token_from_request(request)
        if token is None:
            return HttpResponseBadRequest("Bad Request\n")
        page = int(request.GET.get('page', 1))
        pagination = int(request.GET.get('pagination', 2))

        # Assumption- For now, this will return the list of products only when a valid partner
        # queries for data. The alternative way was to only list thin-air's products if anybody else
        # other than a partner queried.
        request_partner = None
        for partner in Partner.objects.all():
            if partner.token == sha256((token + partner.salt).encode('utf-8')).hexdigest():
                request_partner = partner
                break
        if request_partner is None:
            return HttpResponseBadRequest("Bad Request\n")
        uuid_ta = uuid.UUID(int=0x0)
        uuid_partner = partner.pkey
        prod_list = Product.objects.filter(seller__in=[uuid_ta, uuid_partner])
        total_items = len(prod_list)
        if total_items <= (page - 1)*pagination:
            return HttpResponseBadRequest("Bad Request, Index out of range\n")
        upper_bound_items = min(total_items, page*pagination)
        items = prod_list[(page - 1)*pagination:upper_bound_items]
        myserializer = MySerialiser()
        response = HttpResponse(myserializer.serialize(items))
        response['Cache-Control'] = "no-cache"
        return response

def shop_list(request):
    products_list = Product.objects.filter(count__gt=0)[:3]
    # myserializer = MySerialiser()
    # products_list = myserializer.serialize(products_list)
    context = {'products_list': products_list}
    return render(request, 'shopping_page.html', context)
    pass

@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST':
        # This below part until try-except block is copied from https://stackoverflow.com/a/3244765
        # I doubt there is any other simple way to do it though.
        json_data = json.loads(request.body)
        try:
            product_slug = json_data['slug']
        except KeyError:
            return HttpResponseBadRequest("Malformed data!")
        if request.user.is_authenticated:
            # Do something for authenticated users.
            username = request.user.username # User.objects.get(username=username)
            print(username)
            product = Product.objects.get(slug__exact=product_slug)
            productid = product.pkey
            if Order.objects.filter(customer_id__exact=username).exists():
                pass
                order = Order.objects.get(customer_id__exact=username)
                orderid = order.pk            #products_list = Order.objects.get(count__gt=0)[:3]
                
                print (productid)
                cartitems_in_order = CartItem.objects.filter(order_id__exact=orderid)
                cartitem_of_this_product_found = False
                for cartitem in cartitems_in_order:
                    if cartitem.product_id == productid:
                        cartitem.quantity +=1
                        cartitem.save()
                        cartitem_of_this_product_found = True
                        break
                if not cartitem_of_this_product_found:
                    print ("new_item")
                    new_cartitem = CartItem.objects.create(product_id=productid, quantity=1, order_id=orderid)
                    new_cartitem.save()
            else:
                print ("new_order")
                new_order = Order.objects.create(customer_id=username, placed=False, date_placed=datetime.date.today(),
                                            shipping_address=0, payment=0)
                new_order.save()
                print ("new_item")
                new_cartitem = CartItem.objects.create(product_id=productid, quantity=1, order_id=orderid)
                new_cartitem.save()
            products_list = Product.objects.filter(count__gt=0)[:3]
            # myserializer = MySerialiser()
            # products_list = myserializer.serialize(products_list)
            return HttpResponse()
        else:
            # When user is not logged in.
            # Sep 3, 22:58. Couldn't implement this part properly. Some small implementation detail in javascript,
            # I couldn't figure out. This has changed the code of login.html to attempt to redirect to the shopping list.
            # Running out of time right now. moving onto task 4.2.2
            # this redirects a user to the login page. Once logged in, 
            # the user sees a hyperlink to the product list
            env = Env()
            env.read_env()
            CLIENT_ID = env("GoogleOAuth2ClientID")
            return HttpResponseServerError()
            # return render(request, "login.html", {'ClientId' : CLIENT_ID, 'redirect_to_shop': product_slug})
            pass

# def check_basket(request, order_id):
#     if Order.objects.filter(id__exact=order_id).exists():
#         pass
#         order = Order.objects.get(id=order_id)
#         cartitems_in_order = CartItem.objects.filter(order_id__exact=order_id)
#         context = {"cartitems": cartitems_in_order, "order": order}
#         return render(request, 'basket.html', context)
#     else:
#         return HttpResponseBadRequest("Bad request")