from collections import UserString
from logging import exception

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from payapp.forms import PayForm, RequestPaymentForm
from payapp.models import Transactions, PaymentRequests

from django.contrib.auth import get_user_model

from .models import Transactions, Balance

from django.db import transaction
from decimal import Decimal


import requests
from django.http import JsonResponse

from datetime import datetime

# Create your views here.
def home(request):
    return render(request, 'home.html')

@login_required(login_url='/auth/login')
def dashboard(request):

    if not request.user.is_authenticated:
        return redirect_to_login(request.path,'/auth/login')

    # For setting up the render
    first_name = request.user.first_name
    currency = request.user.currency

    balance = get_balance(request)

    # Get payment requests that are still pending and convert the currency to user's currency
    payment_requests_to_user = PaymentRequests.objects.filter(payee=request.user, status='Pending').order_by(
        'date_requested')
    print(payment_requests_to_user)

    converted_requests = []
    for payment_request in payment_requests_to_user:
        payee_currency = payment_request.amount_requested_currency
        amount = payment_request.amount_requested
        api_url = request.build_absolute_uri('/') + "forex/conversion/" + str(payee_currency) + "/" + str(
            currency) + "/" + str(float(amount))
        api_response = requests.get(api_url).json()
        payment_request.amount_requested_currency = currency
        payment_request.amount_requested = api_response['out_currency']
        converted_requests.append(payment_request)

    payment_requests_from_user = PaymentRequests.objects.filter(request_from=request.user).exclude(status='Pending').order_by('-date_requested')

    payment_requests_from_user_unpaid = PaymentRequests.objects.filter(request_from=request.user, status='Pending').order_by('-date_requested')



    # Getting the transaction history and putting it in a more readable format
    transaction_history = []

    # Transactions where the user is the sender (from_user)
    transaction_history_to = Transactions.objects.filter(from_user=request.user).order_by('-datetime')
    for txn in transaction_history_to:
        transaction_history.append((
            -txn.amount_paid,  # Negated amount paid
            txn.amount_paid_currency,
            txn.datetime.strftime("%d/%m/%Y %H:%M:%S"),
            txn.to_user.username,  # 'To whom' (Only if paying someone)
            None  # 'From whom' will not be included when the user is the sender
        ))

    # Transactions where the user is the receiver (to_user)
    transaction_history_from = Transactions.objects.filter(to_user=request.user).order_by('-datetime')
    for txn in transaction_history_from:
        transaction_history.append((
            txn.amount_received,
            txn.amount_received_currency,
            txn.datetime.strftime("%d/%m/%Y %H:%M:%S"),
            None,  # 'To whom' will not be included when the user is the receiver
            txn.from_user.username  # 'From whom' (Only if receiving money)
        ))
    # Sort the transaction history by datetime in descending order (latest first)
    transaction_history.sort(key=lambda x: x[2], reverse=True)


    # If the user clicks accept or reject on a transaction
    if request.method == "POST":
        request_id = request.POST['request_id']
        status = request.POST['status_' + str(request_id)]

        # Check if status is valid
        if status not in ['accept', 'reject']:
            return HttpResponse("Invalid status", status=400)

        if status == 'accept':
            try:
                payment_request = PaymentRequests.objects.get(id=request_id)

                # Prevent duplicate payments on reload
                if payment_request.status != 'Pending':
                    return redirect('/dashboard') # Redirect because we don't want to pass in the form

                payee = payment_request.request_from
                payee_currency = payee.currency
                amount = payment_request.amount_requested

                # Converting currency to the user's currency, so we know what to deduct
                api_url = request.build_absolute_uri('/') + "forex/conversion/" + str(payee_currency) + "/" + str(
                    request.user.currency) + "/" + str(float(amount))
                api_response = requests.get(api_url).json()

                try:
                    with transaction.atomic():
                        txn = Transactions.objects.create(
                            to_user=payee,
                            amount_paid_currency=request.user.currency,
                            amount_paid=api_response['out_currency'],
                            amount_received_currency=payee_currency,
                            amount_received=api_response['in_currency'],
                            from_user=request.user,
                        )

                        # Update account balances
                        user_new_balance = Balance.objects.get(user=request.user).balance - Decimal(txn.amount_paid)
                        payee_new_balance = Balance.objects.get(user=payee).balance + Decimal(txn.amount_received)

                        if user_new_balance < 0:
                            raise ValueError("Transaction amount exceeds balance")

                        Balance.objects.filter(user=request.user).update(balance=user_new_balance)
                        Balance.objects.filter(user=payee).update(balance=payee_new_balance)

                        # Change payment request status
                        try:
                            payment_request.status = 'Paid'
                            payment_request.save()
                        except Exception as e:
                            print(e)


                        # Redirect because we don't want to pass in the form
                        return redirect('/dashboard')

                except exception as e:
                    return HttpResponse(f"Error: {e}", status=400)
            except ObjectDoesNotExist:
                print("Payment request not found")
        elif status == 'reject':
            try:
                PaymentRequests.objects.filter(id=request_id).update(status='Rejected')
                return redirect('/dashboard')
            except ObjectDoesNotExist:
                print("Payment request not found")

    return render(request, 'payapp/dashboard.html', {
        'first_name': first_name,
        'currency': currency,
        'balance': balance,
        'payment_requests_to_user': converted_requests,
        'payment_requests_from_user': payment_requests_from_user,
        'payment_requests_from_user_unpaid': payment_requests_from_user_unpaid,
        'transaction_history': transaction_history})

@login_required(login_url='/auth/login')
def pay(request):

    if not request.user.is_authenticated:
        return redirect_to_login(request.path,'/auth/login')

    user_balance = get_balance(request)

    if request.method == "POST":
        form = PayForm(request.POST)

        if form.is_valid():

            # Check if the payee exists in the database, if not return to pay page
            # Also check if multiple people with the same username exists in case it ever happens
            payee, error = get_payee(username=form.cleaned_data['to_user'])
            if error:
                form.add_error(None, error)
                return render(request, 'payapp/pay.html', {'form': form, 'error': error})

            if payee == request.user:
                form.add_error(None, "You cannot pay yourself!")
                return render(request, 'payapp/pay.html', {'form': form, 'error': error})

            amount = form.cleaned_data['amount']

            # Get payee's currency
            payee_currency = payee.currency

            # Ensure that the database updates the balances and rolls back on interruptions
            try:
                with transaction.atomic():

                    # if txn.amount > 2:
                    #     raise ValueError("Transaction amount must be less than or equal to 2")
                    api_url = request.build_absolute_uri('/') + "forex/conversion/" + str(request.user.currency) + "/" + str(payee_currency) + "/" + str(float(amount))
                    api_response = requests.get(api_url).json()

                    txn = Transactions.objects.create(
                        to_user=payee,
                        amount_paid_currency=request.user.currency,
                        amount_paid=api_response['in_currency'],
                        amount_received_currency=payee_currency,
                        amount_received=api_response['out_currency'],
                        from_user=request.user
                    )

                    # Update account balances
                    user_new_balance = Balance.objects.get(user=request.user).balance - Decimal(txn.amount_paid)
                    payee_new_balance = Balance.objects.get(user=payee).balance + Decimal(txn.amount_received)

                    if user_new_balance < 0:
                        raise ValueError("Transaction amount exceeds balance")

                    Balance.objects.filter(user=request.user).update(balance=user_new_balance)
                    Balance.objects.filter(user=payee).update(balance=payee_new_balance)

                return render(request, 'payapp/payment_success.html')
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, 'payapp/pay.html', {'form': form, 'balance': user_balance})
        else:
            form.add_error(None, "Form is invalid")

    form = PayForm(currency=request.user.currency)
    return render(request, 'payapp/pay.html', {'form': form, 'balance': user_balance})


def get_balance(request):
    currency = request.user.currency

    if currency == 'GBP':
        currency_symbol = '£'
    elif currency == 'EUR':
        currency_symbol = '€'
    elif currency == 'USD':
        currency_symbol = '$'
    else:
        currency_symbol = ''

    balance = currency_symbol + str(Balance.objects.get(user=request.user).balance)

    return balance

def get_payee(username):
    try:
        return get_user_model().objects.get(username=username), None
    except get_user_model().DoesNotExist:
        return None, "Payee does not exist"
    except get_user_model().MultipleObjectsReturned:
        return None, "Multiple users with the same username exist"

@login_required(login_url='/auth/login')
def request_payment(request):

    if not request.user.is_authenticated:
        return redirect_to_login(request.path,'/auth/login')

    user_balance = get_balance(request)

    if request.method == "POST":
        form = RequestPaymentForm(request.POST)

        if form.is_valid():
            payee = form.cleaned_data['payee']
            amount = form.cleaned_data['amount']

            # Check if the payee exists in the database, if not return to pay page
            # Also check if multiple people with the same username exists in case it ever happens
            payee, error = get_payee(username=form.cleaned_data['payee'])

            if error:
                form.add_error(None, error)
                return render(request, 'payapp/pay.html', {'form': form, 'error': error})

            if payee == request.user:
                form.add_error(None, "You cannot request a payment to yourself!")
                return render(request, 'payapp/pay.html', {'form': form, 'error': error})


            payment_request = PaymentRequests.objects.create(
                payee=payee,
                request_from=request.user,
                amount_requested_currency=request.user.currency,
                amount_requested=amount,
                status='Pending',
            )

            return render(request, 'payapp/request_success.html')

        else:
            form.add_error(None, "Form is invalid")

    form = RequestPaymentForm(currency=request.user.currency)
    return render(request, 'payapp/request_payment.html', {'form': form, 'balance': user_balance})

@login_required(login_url='/auth/login')
@staff_member_required(login_url='/auth/login')
def admin_dashboard(request):

    if not request.user.is_authenticated:
        return redirect_to_login(request.path,'/auth/login')

    if not request.user.is_staff:
        return redirect('/dashboard')

    transaction_history = Transactions.objects.all().order_by('-datetime')

    # For setting up the render
    first_name = request.user.first_name

    # Get all users
    users = get_user_model().objects.all()

    errors=[]
    if request.method == "POST":
        for user in users:
            is_staff = 'is_staff_' + str(user.id)
            if request.POST.get(is_staff) == 'on':
                user.is_staff = True
                user.save()
            else:
                if user == request.user:
                    errors.append("You cannot unassign yourself as staff!")
                elif user.is_superuser:
                    errors.append("You cannot unassign a superuser: " + user.username)
                else:
                    user.is_staff = False
                    user.save()


    return render(request, 'payapp/admin/admin_dashboard.html', {
        'first_name': first_name,
        'transaction_history': transaction_history,
        'users': users,
        'errors': errors,
    })