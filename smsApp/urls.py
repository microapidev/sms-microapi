from .views import userdetails, sendmessage, translateMessages, sendmessage_infobip, get_recipients_ibp, nuobj_api
from django.urls import path
from .views import create_receipents_details, get_recipient_details, save_recipients_details, sms_list
from rest_framework.schemas.coreapi import AutoSchema
from rest_framework_swagger.views import get_swagger_view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="SMS API",
      default_version='v1',
      description="Test SMS API here",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

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
    path('v1/sms/infobip/send', sendmessage_infobip),
    path('v1/sms/infobip/reports', get_recipients_ibp),
    path('v1/sms/nuobjects/send',nuobj_api),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

