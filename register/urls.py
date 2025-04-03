from django.urls import path
from . import views

app_name = 'register'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('signup_success/', views.signup_success, name='signup_success'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]