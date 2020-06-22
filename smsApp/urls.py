from .views import userdetails,sendmessage
from django.urls import path
from .views import create_receipents_details, get_recipient_details, save_recipients_details
from rest_framework.schemas.coreapi import AutoSchema
from rest_framework_swagger.views import get_swagger_view

doc_view = get_swagger_view(title="SMS API documentation")

urlpatterns = [
    path('user/',userdetails),
    path('sms/',sendmessage),
    path('v1/sms/recipient/create', create_receipents_details),
    path('v1/sms/recipient/save', save_recipients_details),
    path('v1/sms/recipient/all', get_recipient_details),
    # path('doc/', doc_view),
    path('', doc_view),
]
