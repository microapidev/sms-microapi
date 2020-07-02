from .views import sendmessage, translateMessages, userdetails, nuobj_api, GroupList, GroupDetail, GroupCreate, SmsHistoryList, SmsHistoryDetail #sendmessage_infobip, get_recipients_ibp
from django.urls import path
from .views import save_recipients_details, sms_list
from .views import NuobjectsSendMessage, NuobjectsGetBalance, NuobjectsMessageList
from .views import ReceipientCreate, ReceipientList
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
    path('v1/sms/recipient/create', ReceipientCreate.as_view(), name="create-new-recipient"),
    path('v1/sms/recipient/save', save_recipients_details),
    path('v1/sms/recipient/all', ReceipientList.as_view(), name="get-all-recipients"),
    path('v1/sms/message/translate', translateMessages),
    #path('swagger(P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'), #not used for now
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('v1/sms/Twillo_sms_history', sms_list),
    path('v1/sms/sms_history', SmsHistoryList.as_view(), name="history"),
    path('v1/sms/sms_history/<str:pk>', SmsHistoryDetail.as_view(), name="history_"),
    # infobip view
    # path('v1/sms/infobip/send', sendmessage_infobip),
    # path('v1/sms/infobip/reports', get_recipients_ibp),
    path('v1/sms/nuobjects/send',nuobj_api),
    path("v1/sms/list_group/<senderID>", GroupList.as_view(), name="list-group"),
    path("v1/sms/create_group", GroupCreate.as_view(), name="update-group"),
    path("v1/sms/group_update/<str:pk>", GroupDetail.as_view(), name="update-group"),
   #Nuobjects
    path("v1/sms/nuobjects_message_list", NuobjectsMessageList.as_view(), name="nuobjects-message-list"),
    path("v1/sms/nuobjects_send_message/", NuobjectsSendMessage.as_view(), name="nuobjects-send-message"),
    path("v1/sms/nuobjects_get_balance/", NuobjectsGetBalance.as_view(), name="nuobjects-get-balance"),
   #  swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

