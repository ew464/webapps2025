from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)

    POUNDS = "GBP"
    DOLLARS = "USD"
    EUROS = "EUR"
    CURRENCY_CHOICES = [
        (POUNDS, "Pound Sterling"),
        (DOLLARS, "United States Dollars"),
        (EUROS, "Euros"),
    ]

    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=POUNDS,
    )

