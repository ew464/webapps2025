from django.contrib import admin

from payapp.models import Transactions, Balance, PaymentRequests

# Register your models here.
admin.site.register(Transactions)
admin.site.register(Balance)
admin.site.register(PaymentRequests)

