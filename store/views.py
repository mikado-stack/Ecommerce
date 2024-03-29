from argparse import Action
from email.headerregistry import Address
import imp
from itertools import product
from multiprocessing import context
from webbrowser import get
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.http import JsonResponse
import json
import datetime
from django.http import HttpResponseRedirect

from .models import *
from . utils import cookieCart, cartData, guestOrder
from django.urls import reverse_lazy

from django.contrib.auth.views import LoginView
from.forms import *

# imports to register a user.
from django.views.generic import FormView
from .forms import RegisterForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.models import User, auth

# Create your views here.

class CustomLoginView(LoginView):
    template_name = 'store/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('store')
   
   

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username= form.cleaned_data.get('username')
            password1 = form.cleaned_data.get('password1')
             #saving the registered user
            user =form.save()
            new_user = authenticate(username=username, password1=password1)
            if new_user is not None:
                login(request, new_user)
            Customer.objects.create(
                    user = user,
                    name = user.username,
                    email = user.email
                )
            
            messages.success(request, ("Registration successful, please login!"))
            return redirect('login')
    else:
        form = RegisterForm()
         
    return render(request, 'store/register.html', {'form':form})


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            messages.success(request, ("login successful"))
            return redirect('store')
        else:
            messages.info(request, 'Username OR password is incorrect')
            return redirect('login')
        
    context ={}
    return render(request, 'store/login.html', context)
       
        
def logout_user(request):
    logout(request)
    messages.info(request, ("logout successful, please login!"))
    return redirect('home')




def store(request):
     data = cartData(request)
     cartItems = data['cartItems']
     user = request.user
    
     products = Product.objects.all()
     arriv = Arrive.objects.all()
     context = {'products':products, 'cartItems':cartItems, 'user':user, 'arriv':arriv}
     return render(request, 'store/store.html', context)
 
def slides(request):
    slide = Slide.objects.all()
    
    context = {'slide':slide}
     
    return render(request, 'store/carousel.html')

def cart(request):
     data = cartData(request)
     cartItems = data['cartItems']
     order = data['order']
     items = data['items']
               
                
     context = {'cartItems':cartItems, 'order':order, 'items':items, }
     return render(request, 'store/cart.html', context)


def checkout(request):
     
     data = cartData(request)
     cartItems = data['cartItems']
     order = data['order']
     items = data['items']
    
     context = {'cartItems':cartItems, 'order':order, 'items':items,}
     return render(request, 'store/checkout.html', context)
 
def order_confirm(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    context = {'cartItems':cartItems, 'order':order, 'items':items,}
    return render(request, 'store/order_confirm.html', context)
  

def updateItem(request):
     data = json.loads(request.body)
     productId = data['productId']
     action = data['action']
      
     print('Action:', action)
     print('productId:', productId)
     
     customer = request.user.customer
     product = Product.objects.get(id=productId)
     order, created = Order.objects.get_or_create(customer=customer, complete=False)
     orderItem, created = OrderItem.objects.get_or_create(order=order, customer=customer, product=product)
     
     if action == 'add':
          orderItem.quantity = (orderItem.quantity + 1)
     
     elif action == 'remove':
          orderItem.quantity = (orderItem.quantity - 1)
          
     orderItem.save()
     
     if orderItem.quantity <= 0:
          orderItem.delete()
     
     
     return JsonResponse('item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    
    else:
         customer, order = guestOrder(request, data)
         
    
    total = float(data['form']['total'])
    order.transaction_id = transaction_id
        
    if total == float(order.get_cart_total):
             order.complete = True
    order.save()
    
    if order.shipping == True:
         ShippingAddress.objects.create(
                  customer=customer,
                  order=order,
                  address=data['shipping']['address'],
                  city=data['shipping']['city'],
                  state=data['shipping']['state'],
                  zipcode=data['shipping']['zipcode'],
               )
         
         
    return JsonResponse('payment complete', safe=False)


def product_details(request, id):
    data = cartData(request)
    cartItems = data['cartItems']
    product = Product.objects.get(id = id)
 
    return render(request, 'store/product_details.html', {'product':product, 'cartItems':cartItems})



def contact(request):
    if request.method =="POST":
        contact = Contact()
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        contact.name=name
        contact.email=email
        contact.subject=subject
        contact.body=body
        contact.save()
        messages.info(request, 'Comment submitted successfully, you will be contacted via your email')
        return redirect('store')
    return render(request, 'store/contact.html')

# The search function

def search(request):
    if request.method =="POST":
        searched =request.POST['searched']
        data = cartData(request)
        cartItems = data['cartItems']
        if searched:
            product = Product.objects.filter(name__icontains=searched)
            messages.info(request, 'Search successful')
            return render(request, 'store/search.html', {'searched':searched,'product':product,'cartItems':cartItems})
    
        else:
            messages.info(request, 'No information to show')
            return render(request, 'store/search.html', {})
    
# def like_product(request):
#     user = request.user
#     if request.method == 'POST':
#         product_id = request.POST.get('product_id')
#         product = Product.objects.get(id=product_id)

#         if user in product.liked.all():
#             product.liked.remove(user)
        
#         like, created = Like.objects.get_or_create(user=user, product_id=product_id)

#         if not created:
#             if like.value == 'like':
#                 like.value = 'unlike'
#             else:
#                 like.value = 'like'

#         like.save()
#     return redirect('store:product_details.html')

def pop(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Pop.objects.get_or_create(customer=customer, )
    
    else:
         customer, order = guestOrder(request, data)
         
    if request.method == 'POST':
        form = Popform(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/") 
    else:
        form = Popform
        
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    context = {'cartItems':cartItems, 'order':order, 'items':items, 'form':form}
    return render(request, 'store/pop.html', context)
   

def play(request):
   
    return render(request, 'store/play.html')


# def accountSettings(request):
#     customer = request.user.customer
#     form = CustomerForm(instance=customer)
    
#     if request.method == 'POST':
#         form = CustomerForm(request.POST, request.FILES,instance=customer)
#         if form.is_valid():
#             form.save
#             messages.success(request, ("Profile updated successfully"))
#             return redirect('profile')
            
#     context = {'form':form}
#     return render(request, 'store/account_settings.html', context)

def profile(request):
    context = {'user':request.user}
    return render(request, 'store/profile.html', context)

def accountSettings(request):
  customer = request.user.customer
  form = CustomerForm(instance=customer)

  if request.method == 'POST':
    form = CustomerForm(request.POST, request.FILES,instance=customer)
    if form.is_valid():
      form.save()
      messages.success(request, ("Profile updated successfully"))
      return redirect('profile')
   

  context = {'form':form}
  return render(request, 'store/account_settings.html', context)
  
