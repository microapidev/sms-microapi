from .views import userdetails, sendmessage, translateMessages, nuobj_api #sendmessage_infobip, get_recipients_ibp
from django.urls import path
from .views import create_receipents_details, get_recipient_details, save_recipients_details, sms_list
from rest_framework.schemas.coreapi import AutoSchema
from rest_framework_swagger.views import get_swagger_view

app_name = 'smsApp'
doc_view = get_swagger_view(title="SMS API documentation")
urlpatterns = [
    path('user/',userdetails),
    path('sms/',sendmessage),
    path('v1/sms/recipient/create', create_receipents_details),
    path('v1/sms/recipient/save', save_recipients_details),
    path('v1/sms/recipient/all', get_recipient_details),
    path('v1/sms/message/translate', translateMessages),
    path('v1/sms/message/history', sms_list),
    # path('doc/', doc_view),
    path('', doc_view),
    # infobip view
    # path('v1/sms/infobip/send', sendmessage_infobip),
    # path('v1/sms/infobip/reports', get_recipients_ibp),
    path('v1/sms/nuobjects/send',nuobj_api),
]

