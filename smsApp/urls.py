<<<<<<< HEAD
from .views import sendmessage, translateMessages, nuobj_api, GroupList, GroupDetail, GroupCreate, SmsHistoryList, SmsHistoryDetail #sendmessage_infobip, get_recipients_ibp
from django.urls import path
from .views import NuobjectsSendMessage, NuobjectsGetBalance, NuobjectsMessageList
from .views import ReceipientCreate, ReceipientList, RecipientDetail
from .views import InfobipSendMessage, InfobipSingleMessage, InfobipMessageList
=======
from .views import sendmessage, translateMessages, userdetails, nuobj_api, TwilioSendSms, GroupList, GroupBySenderList, GroupDetail, GroupCreate, GroupNumbersList,GroupNumbersCreate, GroupNumbersDetail, SmsHistoryList, SmsHistoryDetail #sendmessage_infobip, get_recipients_ibp
from django.urls import path
from .views import create_receipents_details, save_recipients_details, sms_list  #get_recipient_details
>>>>>>> d082962bcb92812fe57bdb0d8098994aa7b241cc
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
#  path('user/',userdetails),
   path('sms/',sendmessage),

   #Recipient Views
   path('v1/sms/recipient/create', ReceipientCreate.as_view(), name="create-new-recipient"),
   path('v1/sms/recipient/all', ReceipientList.as_view(), name="get-all-recipients"),
   path("v1/sms/recipient/<str:pk>", RecipientDetail.as_view(), name="update-recipient"),
   
   #History Views, Which hostory
   path('v1/sms/sms_history', SmsHistoryList.as_view(), name="history"),
   path('v1/sms/sms_history/<str:pk>', SmsHistoryDetail.as_view(), name="history_"),
   
   #Nuobjects Views
   path("v1/sms/nuobjects_message_list", NuobjectsMessageList.as_view(), name="nuobjects-message-list"),
   path("v1/sms/nuobjects_send_message/", NuobjectsSendMessage.as_view(), name="nuobjects-send-message"),
   path("v1/sms/nuobjects_get_balance/", NuobjectsGetBalance.as_view(), name="nuobjects-get-balance"),
   
   #Infobip Views
   path("v1/sms/infobip/send_sms", InfobipSendMessage.as_view(), name="infobip-send-message"),
   path("v1/sms/infobip/view_all_sms", InfobipMessageList.as_view(), name="infobip-sent-messages"),

   #Twillo Views
   path("v1/sms/Twillo_send_sms", sendmessage),
   path('v1/sms/Twillo_sms_history', sms_list),
   path('v1/sms/twilio_send_single', TwilioSendSms.as_view(), name="sendsms"),

   #swagger docs and etc
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   #path('swagger(P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'), #not used for now
   path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
   #Message translation
   path('v1/sms/message/translate', translateMessages),

   #Group Views
   path("v1/sms/list_group", GroupList.as_view(), name="list-group"),
   path("v1/sms/list_group/<senderID>", GroupBySenderList.as_view(), name="list-group"),
   path("v1/sms/create_group", GroupCreate.as_view(), name="update-group"),
   path("v1/sms/group_update/<str:pk>", GroupDetail.as_view(), name="update-group"),
   path("v1/sms/group_recipient/", GroupNumbersList.as_view(), name="group-numbers"),
   path("v1/sms/group_recipient/create", GroupNumbersCreate.as_view(), name="create-group-numbers"),
   path("v1/sms/group_number/<senderID>", GroupNumbersDetail.as_view(), name="update-group-umbers"),

]

