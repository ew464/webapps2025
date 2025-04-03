from django.db import models
from django.contrib.auth import get_user_model

class Balance(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

# Create your models here.
class Transactions(models.Model):
    from_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="from_user", null=False)
    to_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="to_user", null=False)
    amount_paid_currency = models.CharField(max_length=3, choices=get_user_model().CURRENCY_CHOICES, null=False)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    amount_received_currency = models.CharField(max_length=3, choices=get_user_model().CURRENCY_CHOICES, null=False)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING,
    )

    datetime = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Transactions"

class PaymentRequests(models.Model):
    payee = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="user", null=False)
    request_from = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="request_from", null=False)
    amount_requested_currency = models.CharField(max_length=3, choices=get_user_model().CURRENCY_CHOICES, null=False)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    PENDING = "PENDING"
    REJECTED = "REJECTED"
    PAID = "PAID"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (REJECTED, "Rejected"),
        (PAID, "Paid"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING,
        null=False,
    )

    date_requested = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Payment Requests"