from .views import sendmessage, translateMessages,  nuobj_api, CreateUser, ListUser, VerifyAccount #sendmessage_infobip, get_recipients_ibp
from django.urls import path
from .views import create_receipents_details, get_recipient_details, save_recipients_details, sms_list
from rest_framework.schemas.coreapi import AutoSchema
from rest_framework_swagger.views import get_swagger_view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls

#doc_view = get_swagger_view(title="SMS API documentation") #This generator is no longer used
schema_view = get_schema_view(
   openapi.Info(
      title="SMS API",
      default_version='v1',
      description="""
      SMS API testing - This is done using PostMan Testing tool. To start, you need to register using the '/v1/register endpoint'. Using a key-value instance, 
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
    path('user/list', ListUser.as_view(), name="userlist"),
    path("v1/register/", CreateUser.as_view(), name="register"),
    path("v1/verify/", VerifyAccount.as_view(), name="register"),
    path('sms/', sendmessage),
    path('v1/sms/recipient/create', create_receipents_details),
    path('v1/sms/recipient/save', save_recipients_details),
    path('v1/sms/recipient/all', get_recipient_details),
    path('v1/sms/message/translate', translateMessages),
    path('v1/api-token-auth', obtain_auth_token),
    #path('doc/', doc_view), #oldswagger generator endpoint
    #path('', doc_view), #old swagger generator endpoint
    #path('swagger(P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'), #not used for now
   #  path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('v1/sms/message/history', sms_list),
    # infobip view
    # path('v1/sms/infobip/send', sendmessage_infobip),
    # path('v1/sms/infobip/reports', get_recipients_ibp),
    path('v1/sms/nuobjects/send',nuobj_api),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', include_docs_urls(title='SMS API', description=
    """
        SMS API testing - This is done using PostMan Testing tool. To start, you need to register using the '/v1/register endpoint'. Using a key-value instance, 
        post your email, phoneNumber, name, password with the former as the respective keys, also specify content-type and make sure it is set to application/json.
        Set the HTTP Method to post and hit send. Your account has been created. Next is to get your token via 'v1/api-token-auth/' endpoint using the key-value instance 
        of username and password (username being your email address). Copy the given token. To test any endpoint, you need to add your token to the header tab using key-value. 
        in the format {"Authorization": "Token <your token you copied>"}. LET'S TEST!!!."""
    ,permission_classes=(permissions.AllowAny,)))
]

