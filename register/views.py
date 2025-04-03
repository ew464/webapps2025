from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import redirect

from payapp.models import Balance
from .forms import RegisterForm

from django.db import transaction

import templates

import sys

# Create your views here.
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Make sure the balance is created when user is created
            try:
                with transaction.atomic():
                    user_instance = form.save() # Add the user

                    if user_instance.currency == 'GBP':
                        default_balance = 750
                    elif user_instance.currency == 'USD':
                        default_balance = 1000
                    elif user_instance.currency == 'EUR':
                        default_balance = 1250
                    else:
                        default_balance = 0

                    balance = Balance.objects.create(user=user_instance, balance=default_balance)

                return redirect('/auth/signup_success')
            except Exception as e:
                form.add_error(None, str(e))
        else:
            return render(request, 'register/register.html', {'form':form, })

    else:
        form = RegisterForm()

    form = RegisterForm()
    return render(request, 'register/register.html', {'form': form})

def signup_success(request):
    # Redirect to home page if they did not come from the register page
    if 'register' not in request.META.get('HTTP_REFERER', ''):
        return redirect('/')

    # Stay on the page if they were redirected from a successful registration
    return render(request, 'register/signup_success.html')

def user_login(request):

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                return redirect('/dashboard')
            else:
                form.add_error(None, "Invalid username or password")
        else:
            return render(request, 'register/login.html', {'form': form})

    form = AuthenticationForm()
    return render(request, 'register/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return render(request, 'register/logged_out.html')