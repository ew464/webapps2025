from django import forms
from payapp.models import Transactions, PaymentRequests


class PayForm(forms.Form):
    to_user = forms.CharField(max_length=100, label="Payee (Username)")
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        currency = kwargs.pop('currency', 'GBP')
        super().__init__(*args, **kwargs)
        self.fields['amount'].label = f"Amount ({currency})"

    class Meta:
        model = Transactions
        fields = ['to_user', 'amount']


class RequestPaymentForm(forms.Form):
    payee = forms.CharField(max_length=100, label="Payee (Username)")
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        currency = kwargs.pop('currency', 'GBP')
        super().__init__(*args, **kwargs)
        self.fields['amount'].label = f"Amount ({currency})"

    class Meta:
        model = PaymentRequests
        fields = ['payee', 'amount_requested']