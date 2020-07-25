from django.urls import path
from .views import SendSingMsgCreate, TransactionID, GroupTransactionID
from .views import RecipientCreate, RecipientList, RecipientDetail, RecipientsForUser
from .views import InfobipSendMessage, InfobipSingleMessage, InfobipMessageList, InfobipSendMessage2
from .views import translateMessages, MessageDelete, MessageCounter, TwilioSendSms, sms_list
from .views import TeleSignSingleSms, TeleSignMessageList, TeleSignTransactionID3
from .views import TeleSignCollectionSms, MessageRecall
from .views import GroupList, GroupBySenderList, GroupDetail, GroupCreate, GroupDelete, GroupNumbersList, GroupNumbersBySenderList,  GroupNumbersCreate, update_group_number, GroupNumbersDetail
from .views import SmsHistoryList, SmsHistoryDetail, SendGroupSms, SendFlashSms, MessageList, UserList
from .views import SenderDetailsCreate, SenderRegister, SenderDetailsUpdate, SenderDetailsList, SenderDetailsDelete
from django.urls import path
from .views import create_receipents_details, save_recipients_details  #get_recipient_details
from rest_framework.schemas.coreapi import AutoSchema
from rest_framework_swagger.views import get_swagger_view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.documentation import include_docs_urls
import logging

logger = logging.getLogger(__name__)

logger.error("In urls.py for sms api")

schema_view = get_schema_view(
   openapi.Info(
      title="SMS API",
      default_version='v1',
      description="""To begin, register your unique userID via `/v2/sms/user_register`. Next, go to the config endpoint via `/v2/sms/config/add_config` to setup your credentials before proceeding to using the Send group endpoint to send single or group messages. NOTE: YOUR FIRST REGISTERED SERVICE IS SET AS DEFAULT. To change default, visit the `/v2/sms/config/update_config` endpoint. To view the status of a sent message, visit `/v2/sms/message_status/{Token}`
      """,
      # terms_of_service="https://www.google.com/policies/terms/",
      # contact=openapi.Contact(email="contact@snippets.local"),
      # license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
   # Config
   path("v2/sms/user_register", SenderRegister.as_view(), name="register"),
   path("v2/sms/config/add_config", SenderDetailsCreate.as_view(), name="configure"),
   path("v2/sms/config/update_config", SenderDetailsUpdate.as_view(), name="send-one-msg"),
   path("v2/sms/config/view_config/<senderID>", SenderDetailsList.as_view(), name="send-one-msg"),
   # path("v2/sms/config/delete_config", SenderDetailsDelete.as_view(), name="send-one-msg"),s

   #MessageStatus
   path("v2/sms/message_recall/<taskID>", MessageRecall.as_view(), name="recall-message"),

   #MessageStatus
   # path("v2/sms/message_status/single/<str:messageID>", TransactionID.as_view(), name="message-status"),
   path("v2/sms/message_status/<str:Token>", GroupTransactionID.as_view(), name="groupmsg-status"),

   #sendsms
   path("v2/sms/send/send_single_msg", SendSingMsgCreate.as_view(), name="send-one-msg"),
   path("v2/sms/send/send_group_sms", SendGroupSms.as_view(), name="send-group-sms"),
   # path("v2/sms/send/send_flash_sms",  SendFlashSms.as_view(), name="send-flash-sms"),

   #admin
   # path('v2/sms/admin/messages', MessageList.as_view(), name="view-all-messages"),
   # path('v2/sms/admin/users', UserList.as_view(), name="view-all-users"),

   #messageDelete
   # path("v1/sms/message/delete/<transactionID>", MessageDelete.as_view(), name="delete-message"),
   # path("v1/sms/message/<userID>", MessageCounter.as_view(), name="count-message"),

   #Recipient Views
   # path('v1/sms/recipients/create', RecipientCreate.as_view(), name="create-new-recipient"),
   # path('v1/sms/recipients/<str:userID>', RecipientsForUser.as_view(), name="get-user-recipients"),
   # path("v1/sms/recipients/<str:recipientNumber>", RecipientDetail.as_view(), name="update-recipient"),
   
   #History Views, General Histories
   path('v2/sms/history/<str:senderID>', SmsHistoryList.as_view(), name="history"),

   #TeleSign Views
   # path("v1/sms/telesign/group_sms", TeleSignGroupSms.as_view(), name="telesign-group-message"),
   # path("v1/sms/telesign/send_sms", TeleSignSingleSms.as_view(), name="telesign-send-message"),
   # path("v1/sms/telesign/view_all_sms", TeleSignMessageList.as_view(), name="telesign-sent-messages"),
   # path("v1/sms/telesign/<transactionID>", TeleSignTransactionID3.as_view(), name="telesign-sent-messages3"),

   #Infobip Views
   # path("v1/sms/infobip/send_sms", InfobipSendMessage.as_view(), name="infobip-send-message"),
   # path("v1/sms/infobip/send_sms2", InfobipSendMessage2.as_view(), name="infobip-send-message2"),
   #path("v1/sms/infobip/send_group_sms", InfobipGroupMessage.as_view(), name="infobip-group-message"),

   # path("v1/sms/infobip/view_all_sms", InfobipMessageList.as_view(), name="infobip-sent-messages"),
   # path("v1/sms/infobip/view_all_sms/<str:senderID>", InfobipSingleMessage.as_view(), name="infobip-sent-messages"),
   
   #Twillo Views path
   # path('v1/sms/twilio_sms_history', sms_list),
   # path('v1/sms/twilio_send_single', TwilioSendSms.as_view(), name="sendsms"),
   #path('v1/sms/twilio_send_group', send_group_twilio),


   #swagger docs and etc
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
   path('coreapi', include_docs_urls(title='SMS API', description=
   """
       To begin, register your unique userID via '/v2/sms/user_register'. Next, go to the config endpoint via `/v2/sms/config/add_config` to setup your credentials before proceeding to using the Send group endpoint to send single or group messages. NOTE: YOUR FIRST REGISTERED SERVICE IS SET AS DEFAULT. To change default, visit the `/v2/sms/config/update_config` endpoint. To view the status of a sent message, visit /v2/sms/message_status/{Token}
   """
   ,permission_classes=(permissions.AllowAny,))),
    
   #Message translation
   # path('v1/sms/message/translate', translateMessages),

   #Group Views
   # path("v1/sms/list_group", GroupList.as_view(), name="list-group"),
   # path("v1/sms/list_group/<senderID>", GroupBySenderList.as_view(), name="list-group"),
   # path("v1/sms/create_group", GroupCreate.as_view(), name="update-group"),
   # path("v1/sms/group_update/<str:pk>", GroupDetail.as_view(), name="update-group"),
   # path("v1/sms/group_delete/<str:groupname>", GroupDelete.as_view(), name="delete-group"),
   # path("v1/sms/group_recipient/", GroupNumbersList.as_view(), name="group-numbers"),
   # path("v1/sms/group_recipient/create", GroupNumbersCreate.as_view(), name="create-group-numbers"),
   # path("v1/sms/group_recipient_list/<str:groupname>", GroupNumbersBySenderList.as_view(), name="list-group-numbers-senderID"),
   # path("v1/sms/group_recipient_update/<str:pk>", update_group_number, name="update-group-umbers"),
   # path("v1/sms/group_recipient_delete/<str:pk>", GroupNumbersDetail.as_view(), name="update-group-umbers"),
   
]

logger.error("at the end of urls.py for sms api")
