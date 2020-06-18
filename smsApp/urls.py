from django.urls import path

from .views import create_receipents_details

urlpatterns = [
    path('v1/sms/receipent/create', create_receipents_details),
]
