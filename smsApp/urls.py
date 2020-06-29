from .views import sendmessage, translateMessages, sendmessage_infobip, get_recipients_ibp, nuobj_api, CreateUser, ListUser
from django.urls import path
from .views import create_receipents_details, get_recipient_details, save_recipients_details, sms_list
from rest_framework.schemas.coreapi import AutoSchema
from rest_framework_swagger.views import get_swagger_view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

#doc_view = get_swagger_view(title="SMS API documentation") #This generator is no longer used
schema_view = get_schema_view(
   openapi.Info(
      title="SMS API",
      default_version='v1',
      description="Test the endpoints of miroapi's SMS API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('user/', CreateUser.as_view(), name="userdet"),
    path('user/list', ListUser.as_view(), name="userlist"),
    path('sms/',sendmessage),
    path('v1/sms/recipient/create', create_receipents_details),
    path('v1/sms/recipient/save', save_recipients_details),
    path('v1/sms/recipient/all', get_recipient_details),
    path('v1/sms/message/translate', translateMessages),
    #path('doc/', doc_view), #oldswagger generator endpoint
    #path('', doc_view), #old swagger generator endpoint
    #path('swagger(P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'), #not used for now
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('v1/sms/message/history', sms_list),
    # infobip view
    path('v1/sms/infobip/send', sendmessage_infobip),
    path('v1/sms/infobip/reports', get_recipients_ibp),
    path('v1/sms/nuobjects/send',nuobj_api),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

