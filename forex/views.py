from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view

from register.models import User
from decimal import Decimal, ROUND_HALF_UP

@api_view(['GET'])
def getData(request, currency1, currency2, amount_of_currency1):

    currencies = [currency for currency, name in User.CURRENCY_CHOICES]

    # Check if currencies are valid
    if currency1.upper() not in currencies:
        return HttpResponse("Currency \"" + str(currency1.upper()) + "\" not found")
    if currency2.upper() not in currencies:
        return HttpResponse("Currency \"" + str(currency2.upper()) + "\" not found")

    # Double-checking to see if amount of currency is an integer
    if type(amount_of_currency1) != float:
        return HttpResponse("Invalid amount of currency 1: " + amount_of_currency1)

    amount_of_currency2 = exchange(currency1.upper(), currency2.upper(), amount_of_currency1)

    response = {"in_currency": amount_of_currency1, "out_currency": amount_of_currency2,}

    return JsonResponse(response)

def exchange(currency1, currency2, amount_of_currency1):
    conversion_rates = {
        'GBP': {
            'USD': 1.29,
            'EUR': 1.19,
        },
        'USD': {
            'GBP': 1 / 1.29,
            'EUR': 1.19 / 1.29,
        },
        'EUR': {
            'GBP': 1 / 1.19,
            'USD': 1.29 / 1.19,
        }
    }

    # Handle the case where there is no conversion
    if currency1 == currency2:
        return amount_of_currency1

    conversion_rate = conversion_rates[currency1].get(currency2)

    amount_of_currency2 = amount_of_currency1 * conversion_rate
    amount_of_currency2 = float(Decimal(amount_of_currency2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


    return amount_of_currency2
