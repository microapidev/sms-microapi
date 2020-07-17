from django.urls import path
from .views import SendSingMsgCreate
from .views import RecipientCreate, RecipientList, RecipientDetail, RecipientsForUser
<<<<<<< HEAD
from .views import InfobipSendMessage, InfobipSingleMessage, InfobipMessageList,  InfobipSendMessage2 #InfobipGroupMessage,
from .views import translateMessages, MessageDelete, MessageCounter
from .views import TeleSignSingleSms, TeleSignMessageList, TeleSignTransactionID3 #TeleSignGroupSms, 
from .views import TwilioSendSms, sms_list, SendGroupSms #send_group_twilio,  
from .views import GroupList, GroupBySenderList, GroupDetail, GroupCreate, GroupDelete, GroupNumbersList, GroupNumbersBySenderList, GroupNumbersCreate, update_group_number, GroupNumbersDetail, TransactionID
from .views import SmsHistoryList, SmsHistoryDetail
=======
from .views import InfobipSendMessage, InfobipSingleMessage, InfobipMessageList, InfobipSendMessage2
from .views import translateMessages, MessageDelete, MessageCounter, TwilioSendSms, sms_list
from .views import TeleSignSingleSms, TeleSignMessageList, TeleSignTransactionID3
from .views import TeleSignCollectionSms #,send_group_twilio#InfobipGroupMessage
from .views import GroupList, GroupBySenderList, GroupDetail, GroupCreate, GroupDelete, GroupNumbersList, GroupNumbersBySenderList, GroupNumbersCreate, update_group_number, GroupNumbersDetail
from .views import SmsHistoryList, SmsHistoryDetail, SendGroupSms
>>>>>>> 79f7b249e624cd301a33de17356b78bb09747037
from django.urls import path
from .views import create_receipents_details, save_recipients_details  #get_recipient_details
from rest_framework.schemas.coreapi import AutoSchema
from rest_framework_swagger.views import get_swagger_view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.documentation import include_docs_urls


schema_view = get_schema_view(
   openapi.Info(
      title="SMS API",
      default_version='v1',
      description="""SMS API testing - This is done using PostMan Testing tool. To start, you need to register using the '/v1/register endpoint'. Using a key-value instance, 
        post your email, phoneNumber, name, password with the former as the respective keys, also specify content-type and make sure it is set to application/json.
        Set the HTTP Method to post and hit send. Your account has been created. Next is to get your token via 'v1/api-token-auth/' endpoint using the key-value instance 
        of username and password (username being your email address). Copy the given token. To test any endpoint, you need to add your token to the header tab using key-value. 
        in the format {"Authorization": "Token <your token you copied>"}. LET'S TEST!!!.
      """,
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
   #MessageStatus
   path("v2/sms/messagestatus/<str:msgID>", TransactionID.as_view(), name="message-status"),

   #sendsms
   path("v2/sms/send_single_msg", SendSingMsgCreate.as_view(), name="send-one-msg"),
   path("v2/sms/send_group_sms", SendGroupSms.as_view(), name="send-group-sms"),
   #messageDelete
   path("v1/sms/message/delete/<transactionID>", MessageDelete.as_view(), name="delete-message"),
   path("v1/sms/message/<userID>", MessageCounter.as_view(), name="count-message"),

   #Recipient Views
   path('v1/sms/recipients/create', RecipientCreate.as_view(), name="create-new-recipient"),
   path('v1/sms/recipients/all', RecipientList.as_view(), name="get-all-recipients"),
   path('v1/sms/recipients/<str:userID>', RecipientsForUser.as_view(), name="get-user-recipients"),
   path("v1/sms/recipients/<str:recipientNumber>", RecipientDetail.as_view(), name="update-recipient"),
   
   #History Views, General Histories
   path('v1/sms/sms_history/<str:senderID>', SmsHistoryList.as_view(), name="history"),

   #TeleSign Views
<<<<<<< HEAD
   # path("v1/sms/telesign/group_sms", TeleSignGroupSms.as_view(), name="telesign-group-message"),
=======
   path("v1/sms/telesign/group_sms", TeleSignCollectionSms.as_view(), name="telesign-group-message"),
>>>>>>> 79f7b249e624cd301a33de17356b78bb09747037
   path("v1/sms/telesign/send_sms", TeleSignSingleSms.as_view(), name="telesign-send-message"),
   path("v1/sms/telesign/view_all_sms", TeleSignMessageList.as_view(), name="telesign-sent-messages"),
   path("v1/sms/telesign/<transactionID>", TeleSignTransactionID3.as_view(), name="telesign-sent-messages3"),

   #Infobip Views
   path("v1/sms/infobip/send_sms", InfobipSendMessage.as_view(), name="infobip-send-message"),
   # path("v1/sms/infobip/send_sms2", InfobipSendMessage2.as_view(), name="infobip-send-message2"),
   # path("v1/sms/infobip/send_group_sms", InfobipGroupMessage.as_view(), name="infobip-group-message"),
   path("v1/sms/infobip/view_all_sms", InfobipMessageList.as_view(), name="infobip-sent-messages"),
   path("v1/sms/infobip/view_all_sms/<str:senderID>", InfobipSingleMessage.as_view(), name="infobip-sent-messages"),
   
   #Twillo Views path
   path('v1/sms/Twillo_sms_history', sms_list),
   path('v1/sms/twilio_send_single', TwilioSendSms.as_view(), name="sendsms"),
   #path('v1/sms/twilio_send_group', send_group_twilio),


   #swagger docs and etc
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
   path('', include_docs_urls(title='SMS API', description=
   """
      SMS API testing - This is done using PostMan Testing tool. To start, all you need to do is have a senderID or userID. Once supplied, it would be used to 
      identify all transactions done by you. To send a single sms using an service,visit the respective endpoint and follow the instructions based on format and 
      request to be sent. Remember senderID == userID, and this is personally generated. LET'S TEST!!!."""
   ,permission_classes=(permissions.AllowAny,))),
    
   #Message translation
   path('v1/sms/message/translate', translateMessages),

   #Group Views
   path("v1/sms/list_group", GroupList.as_view(), name="list-group"),
   path("v1/sms/list_group/<senderID>", GroupBySenderList.as_view(), name="list-group"),
   path("v1/sms/create_group", GroupCreate.as_view(), name="update-group"),
   path("v1/sms/group_update/<str:pk>", GroupDetail.as_view(), name="update-group"),
   path("v1/sms/group_delete/<str:groupname>", GroupDelete.as_view(), name="delete-group"),
   path("v1/sms/group_recipient/", GroupNumbersList.as_view(), name="group-numbers"),
   path("v1/sms/group_recipient/create", GroupNumbersCreate.as_view(), name="create-group-numbers"),
   path("v1/sms/group_recipient_list/<str:senderID>", GroupNumbersBySenderList.as_view(), name="list-group-numbers-senderID"),
   path("v1/sms/group_recipient_update/<str:pk>", update_group_number, name="update-group-umbers"),
   path("v1/sms/group_recipient_delete/<str:pk>", GroupNumbersDetail.as_view(), name="update-group-umbers"),
   
]

