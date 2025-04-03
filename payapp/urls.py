from django.urls import path
from . import views

app_name = 'payapp'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('pay/', views.pay, name='pay'),
    path('request_payment/', views.request_payment, name='request_payment'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]