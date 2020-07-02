from .views import sendmessage, translateMessages, userdetails, nuobj_api, GroupList, GroupDetail, GroupCreate, \
    SmsHistoryList, SmsHistoryDetail, send_with_infobip  # sendmessage_infobip, get_recipients_ibp
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
    path('user/',userdetails),
    path('sms/',sendmessage),
    path('v1/sms/recipient/create', create_receipents_details),
    path('v1/sms/recipient/save', save_recipients_details),
    path('v1/sms/recipient/all', get_recipient_details),
    path('v1/sms/message/translate', translateMessages),
    #path('swagger(P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'), #not used for now
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('v1/sms/Twillo_sms_history', sms_list),
    path('v1/sms/sms_history', SmsHistoryList.as_view(), name="history"),
    path('v1/sms/sms_history/<str:pk>', SmsHistoryDetail.as_view(), name="history_"),
    # infobip view
    path('v1/sms/infobip/send_sms', send_with_infobip),
    # path('v1/sms/infobip/reports', get_recipients_ibp),
    path('v1/sms/nuobjects/send',nuobj_api),
    path("v1/sms/list_group", GroupList.as_view(), name="list-group"),
    path("v1/sms/create_group", GroupCreate.as_view(), name="update-group"),
    path("v1/sms/group_update/<str:pk>", GroupDetail.as_view(), name="update-group"),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

