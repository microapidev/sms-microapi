from .views import userdetails,sendmessage
from django.urls import path

urlpatterns = [
    path('user/',userdetails),
    path('sms/',sendmessage)
]

