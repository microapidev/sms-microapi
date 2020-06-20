from .views import userdetails,sendmessage
from django.urls import path

urlpatterns = [
    path('user/',userdetails),
    path('sms/',sendmessage)
]

from django.urls import path

from .views import create_receipents_details, get_recipient_details, save_recipients_details

urlpatterns = [
    path('v1/sms/recipient/create', create_receipents_details),
    path('v1/sms/recipient/save', save_recipients_details),
    path('v1/sms/recipient/all', get_recipient_details)
]
