from django.urls import path, register_converter
from . import views

class FloatUrlParameterConverter:
    regex = '[0-9]+\.[0-9]+'

    def to_python(selfself, value):
        return float(value)

    def to_url(self, value):
        return str(value)

register_converter(FloatUrlParameterConverter, 'float')
urlpatterns = [
    path('conversion/<str:currency1>/<str:currency2>/<float:amount_of_currency1>', views.getData, name='index'),
]