import requests
from requests.auth import HTTPBasicAuth
from django.shortcuts import render, get_object_or_404, get_list_or_404
from rest_framework.parsers import JSONParser
# from smsApp.models import user
# from smsApp.serializers import UserSerializer
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework import status
from twilio.rest import Client
from requests_oauthlib import OAuth1Session
import messagebird
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse
from django.http import JsonResponse
from twilio.base.exceptions import TwilioRestException
from urllib.error import HTTPError
import re
import json
import base64
import http.client
import mimetypes
import urllib.parse
from urllib.parse import urlencode
from .models import Recipient, Message, Group, GroupNumbers, SenderDetails, Sender
from .serializers import RecipientSerializer, MessageSerializer, GroupSerializer, GroupNumbersSerializer, GroupNumbersPrimarySerializer
from .serializers import SenderSerializer, SenderDetailsSerializer
from googletrans import Translator
import uuid
import logging
from .tasks import singleMessageSchedule, taskInfobipAsync, taskTelesignAsync, taskTwilioAsync
from smsApi.celery import app as celeryTaskapp
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)

logger.error("In views.py. starting")

# Create your views here.

def translateMsg(content, lang='en'):
    #This will help translate message of customer.
    
    translator = Translator(service_urls=[
        'translate.google.com',
        'translate.google.co.kr',
    ])

    if lang is None:
        lang = 'en'
        translated = translator.translate(text=content, dest=lang)
        content = translated.text
        return content
    else:
        translated = translator.translate(text=content, dest=lang)
        content = translated.text
        return content

#USING CBV TO POST SMS
#Defining a new API that a user can send a single sms while specifying services
class SendSingMsgCreate(generics.CreateAPIView):
    """
    Send SMS to a single recipient
    {
        "senderID" : "",
        "receiver" : "phone number",
        "content" :  "message body"
    }
    """
    logger.error("In single message class")
    
    serializer_class = MessageSerializer

    def post(self, request, *args, **kwargs):

        senderID = request.data.get("senderID")
        sender = get_object_or_404(Sender, senderID=senderID)
        # sender = Sender.objects.get(senderID=senderID)
        # sender.details.get(default=2)
        service = sender.details.get(default=True)
        sid = service.sid
        token = service.token
        service_type = service.service_name
        verified_no = service.verified_no
        print(service, service_type, token, sid, verified_no)
        receiver = request.data.get("receiver")
        content = request.data.get("content")
        language = request.data.get("language")
        regex = re.compile(r'^\+?1?\d{9,15}$')
        original_txt = []
        logger.error("posting to message")
        # print(senderID.service_name) 
        if regex.match(receiver):
            
            if (service_type == 'TW' or service_type == 'TWILIO'):
                
                message_dict = {'senderID':senderID, 'receiver':receiver, 'content':content}


                serializer_message = MessageSerializer(data=message_dict)
                
                client = Client(f"{sid}",
                                f"{token}")
                if serializer_message.is_valid():
                    print('yeah')
                    value = serializer_message.save()
                    value.service_type = 'TW'
                    try:
                        if (language != 'en' or language != None or language != " " ):
                            original_txt.append(content)
                            content = translateMsg(content, language)
                            value.language = language
                            
                            message = client.messages.create(
                                from_=senderID,
                                to=receiver,
                                body=content,
                            )
                        else:
                            message = client.messages.create(
                                from_=senderID,
                                to=receiver,
                                body=content,
                            )
                        if (message.status == 'sent'):
                            value.messageStatus = "S"
                        elif (message.status == 'queued'):
                            value.messageStatus = "P"
                        elif (message.status == 'failed'):
                            value.messageStatus = "F"
                        elif (message.status == 'delivered'):
                            value.messageStatus = "R"
                        else:
                            value.messageStatus = "U"
                        value.transactionID= message.sid
                        value.save()
                        if len(original_txt) != 0:
                            return Response({
                                'success': 'true',
                                "status": f"{message.status}",
                                'message': f"{original_txt[0]}",
                                'data': {
                                    'receiver': f"{receiver}",
                                    # 'userID': f"{senderID}",
                                    'message_sent': f"{content}",
                                    'service_type': 'TWILIO',
                                }
                            }, 200)
                        return Response({
                            'success': 'true',
                            "status": f"{message.status}",
                            'message': 'Message sent',
                            'data': {
                                'receiver': f"{receiver}",
                                # 'userID': f"{senderID}",
                                'message_sent': f"{content}",
                                'service_type': 'TWILIO',
                            }
                        }, 200)

                    except TwilioRestException as e:
                        value.messageStatus = "F"
                        value.transactionID = "500-F"
                        value.language = "en"
                        value.save()
                        return Response({
                            'success': 'False',
                            'message': 'Message not sent',
                            "messageID":f"{value.messageID}",
                            'error': {
                                'error': f"{str(e)}",
                                'recipient': f"{receiver}",
                                'service_type': 'TWILIO',
                                'statusCode': '400',
                                'details': 'The Phone Number is Not registered to Twilio'
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)                             
                return Response({
                    "success": "False",
                    "status": "F",
                    'message': 'Message cannot be sent',
                    "messageID":f"{value.messageID}",
                    'error': {
                        # 'userID': f"{senderID}",
                        'recipient': f"{receiver}",
                        'service_type': 'TWILIO',
                        'statusCode': '400',
                        'details': 'All fields are required, a field is ommitted'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            #Infobip
            elif (service_type.upper() == 'IF' or service_type.upper() == "INFOBIP"):
                logger.error("posting to message in INFOBIP")

                message_dict = {'senderID':senderID, 'receiver':receiver, 'content':content}
                serializer = MessageSerializer(data=message_dict)
                conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
                payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":false}]}" % (senderID, receiver, content)
                # payload =  "{\"messages\":\"[{\"from\":\"{%s}\",\"destinations\":[{\"to\":\"%s\",\"messageId\":\"Stage7-Company\"}],\"text\":\"%s\",\"flash\":false,\"notifyUrl\":\"https://www.example.com/sms/advanced\",\"notifyContentType\":\"application/json\",\"callbackData\":\"DLR callback data\",\"validityPeriod\":720}}" % (senderID, receiver, content)
                # payload = {"from": f"{senderID}", "to":f"{receiver}", "text": f"{content}"}
                if serializer.is_valid():
                    value = serializer.save()
                    value.service_type = 'IF'
                    if (language != 'en' or language != None or language != ""):
                        original_txt.append(content)
                        content = translateMsg(content, language)
                        value.language = language
                        data = {
                            "from": senderID,
                            "to": receiver,
                            "text": content
                        }
                        headers = {
                            'Authorization': 'App %s' % (token),
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                            }
                    else:
                        value.language = "en"
                        data = {
                            "from": senderID,
                            "to": receiver,
                            "text": content
                        }
                        headers = {
                            'Authorization': 'App %s' % (token),
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                            }
                    # r = requests.post("https://jdd8zk.api.infobip.com",
                    #                   data=payload, headers=headers)
                    # response = r.json()
                    value.service_type = 'IF'
                    conn.request("POST", "/sms/2/text/advanced", payload, headers)
                    res = conn.getresponse()
                    data = res.read().decode('utf-8')
                    data = json.loads(data)
                    if res.status == 200:
                        value.transactionID = data["messages"][0]["messageId"]
                        if ( data["messages"][0]["status"]["groupId"] == 1):
                            value.messageStatus = "P"
                        if ( data["messages"][0]["status"]["groupId"] == 2):
                            value.messageStatus = "U"
                        if ( data["messages"][0]["status"]["groupId"] == 3):
                            value.messageStatus = "S"
                        if ( data["messages"][0]["status"]["groupId"] == 4):
                            value.messageStatus = "E"
                        if ( data["messages"][0]["status"]["groupId"] == 5):
                            value.messageStatus = "FR"
                    else:
                        value.messageStatus = "F"
                        return Response("someting went wrong while sending, please try again")
                    value.save()
                    # print(data)
                    if len(original_txt) != 0:
                        return Response({"success":"True", "status": res.status, "message": f"{original_txt[0]}", "messageID":f"{value.messageID}", "data": data})
                    return Response({"success":"True","status": res.status, "message": "", "messageID":f"{value.messageID}", "data": data})
                else:
                    return Response({"message": "Not Valid"})
            
            #For Telesign
            elif (service_type == 'TS' or service_type.upper() == "TELESIGN"):
                logger.error("posting to message in telesign")
                message_dict = {'senderID':senderID, 'receiver':receiver, 'content':content}
                serializer_message = MessageSerializer(data=message_dict)

                api_key = token
                customer_id = sid 
                url = 'https://rest-api.telesign.com/v1/messaging'
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'}
                if serializer_message.is_valid():
                    # print(value)
                    # print("break----")
                    value = serializer_message.save()
                    value.service_type = 'TS'
                    if (language != 'en' or language != None or language != ""):
                        original_txt.append(content)
                        content = translateMsg(content, language)
                        value.language = language
                        data = {
                            'phone_number': receiver,
                            'message': content,
                            'message_type': 'ARN'
                        }
                    else:
                        value.language = "en"
                        data = {
                            'phone_number': receiver,
                            'message': content,
                            'message_type': 'ARN'
                        }

                    r = requests.post(url, 
                                    auth=HTTPBasicAuth(customer_id, api_key), 
                                    data=data, 
                                    headers=headers)
                    response = r.json()
                    if response['status']['code'] == 290:
                        value.service_type = 'TS'
                        value.messageStatus = 'P'
                        value.transactionID = response['reference_id']
                        value.save()
                        if len(original_txt) != 0:
                            return Response({
                                "success": "True",
                                "status": f"{value.messageStatus}",
                                "message": f"{original_txt[0]}",
                                "messageID":f"{value.messageID}",
                                "data": response,
                                "service_type": "TELESIGN"
                                })
                        return Response({
                            "success": "True",
                            "status": f"{value.messageStatus}",
                            "message": "Message Sending",
                            "data": response,
                            "service_type": "TELESIGN"
                            })
                    else:
                        value = serializer_message.save()
                        value.service_type = 'TS'
                        value.messageStatus = 'F'
                        value.receiver = receiver
                        value.transactionID = "500-F"
                        value.save()
                        return Response({
                            "success": "False",
                            "status": "F",
                            "message": "Message Couldnt be sent",
                            "messageID":f"{value.messageID}",
                            "data": response,
                            "service_type": "TELESIGN"})
                else:
                    return Response({"success":"False","message": "Invalid credentials","messageID":f"{value.messageID}","data": "Not Valid", "service type": f"{service_type}"}, status=status.HTTP_400_BAD_REQUEST)
            
            #for MessageBird
            elif (service_type == 'MB' or service_type.upper() == "MESSAGEBIRD"):

                logger.error("posting to message in MessageBird")
                message_dict = {'senderID':senderID, 'receiver':receiver, 'content':content}
                serializer_message = MessageSerializer(data=message_dict)
                Access_key = token
                client = messagebird.Client(Access_key)
                if serializer_message.is_valid():
                    value = serializer_message.save()
                    value.service_type = 'MB'
                    try:
                        if (language != 'en' or language != None or language != ""):
                            original_txt.append(content)
                            content = translateMsg(content, language)
                            value.language = language
                        else:
                            value.language = "en"

                        message = client.message_create(
                            originator=senderID,
                            recipients=[receiver],
                            body=content,
                        )
                        # data = json.loads(message)

                        data = message.__dict__
                        item = data['_recipients']['items'][0].__dict__
                        if data['gateway'] == 10:
                            value.messageStatus = "F"
                            return Response({
                                "success": "false",
                                "status": f"{value.messageStatus}",
                                "message": f"{original_txt[0]}",
                                "messageID":f"{value.messageID}",
                                "data": {
                                    "gaID": f"{data['id']}",
                                    "body": f"{data['body']}",
                                    "reference": f"{data['reference']}",
                                    "recipients": f"{item['recipient']}",
                                    "status": f"{item['status']}"
                                },
                                "service_type": "MessageBird"
                                })
                        elif data['gateway'] == 240:
                            value.messageStatus = "S"
                            return Response({
                                "success": "false",
                                "status": f"{value.messageStatus}",
                                "message": f"{original_txt[0]}",
                                "messageID":f"{value.messageID}",
                                "data": {
                                    "gaID": f"{data['id']}",
                                    "body": f"{data['body']}",
                                    "reference": f"{data['reference']}",
                                    "recipients": f"{item['recipient']}",
                                    "status": f"{item['status']}"
                                },
                                "service_type": "MessageBird"
                                })
                    except messagebird.client.ErrorException as e:
                        data = e.__dict__
                        print(data['errors'])
                        erra = data['errors'][0].__dict__
                        print(erra)
                        value.messageStatus = "F"
                        value.transactionID = "500-F"
                        value.language = "en"
                        value.save()

                        return Response({
                            'success': 'False',
                            'message': 'Message not sent',
                            "messageID":f"{value.messageID}",
                            'error': {
                                # 'userID': f"{senderID}",
                                'recipient': f"{receiver}",
                                'service_type': 'MessageBird',
                                'statusCode': '400',
                                'details': f"{str(e)}"
                            }
                        }, status=status.HTTP_400_BAD_REQUEST) 
                else:
                    return Response({"success":"False","message": "Invalid credentials","messageID":"","data": "Not Valid", "service type": f"{service_type}"}, status=status.HTTP_400_BAD_REQUEST)
            
            #For GatewayAPi
            elif (service_type == 'GA' or service_type.upper() == "GATEWAYAPI"):
                logger.error("posting to message in GatewayAPi")
                message_dict = {'senderID':senderID, 'receiver':receiver, 'content':content}
                serializer_message = MessageSerializer(data=message_dict)
                if serializer_message.is_valid():
                    value = serializer_message.save()
                    value.service_type = 'GA'
                    try:   
                        if (language != 'en' or language != None or language != ""):
                                original_txt.append(content)
                                content = translateMsg(content, language)
                                value.language = language
                        else:
                            value.language = "en"
                        
                        key = sid
                        secret = token
                        gwapi = OAuth1Session(key, client_secret=secret)
                        req = {
                            'recipients': [{'msisdn': f'{receiver}'}],
                            'message': f'{content}',
                            'sender': f'{senderID}',
                        }
                        res = gwapi.post('https://gatewayapi.com/rest/mtsms', json=req)
                        data = res
                        return Response({
                            "success": "True",
                            "status": f"{value.messageStatus}",
                            "message": f"{original_txt[0]}",
                            "messageID":f"{value.messageID}",
                            "data": data,
                            "service_type": "GatewayAPi"
                            })
                    except Exception as e:
                        value.messageStatus = "F"
                        value.transactionID = "500-F"
                        value.language = "en"
                        value.save()
                        # errors = []
                        # for error in e:
                        #     errors.append(e)
                        return Response({
                            'success': 'False',
                            'message': 'Message not sent',
                            "messageID":f"{value.messageID}",
                            'error': {
                                # 'userID': f"{senderID}",
                                'recipient': f"{receiver}",
                                'service_type': 'GatewayAPi',
                                'statusCode': '400',
                                'details': e
                            }
                        }, status=status.HTTP_400_BAD_REQUEST) 
                        
                else:
                    return Response({"success":"False","message": "Invalid credentials","messageID":"","data": "Not Valid", "service type": f"{service_type}"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"success":"False","message": "","messageID":"","data": "N/A", f"service_type {service_type}": "Not Supported"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({f"{receiver}  does not start with +,1,0 or is a single number.": "Not Supported"}, status=status.HTTP_400_BAD_REQUEST)






class MessageDelete(generics.DestroyAPIView):
    """
    To delete simply use: /v1/sms/group_update/groupName
    """
    def get_object(self, transactionID):
        message = Message.objects.filter(transactionID=transactionID)
        return message

    def delete(self, request, transactionID, format=None):
        message = self.get_object(transactionID)
        message.delete()
        return Response({"Item":"Successfully Deleted"},status=status.HTTP_200_OK)


class MessageCounter(generics.DestroyAPIView):
    """
    To delete simply use: /v1/sms/group_update/groupName
    """
    def get_object(self, senderID):
        messages = Message.objects.filter(senderID=senderID)
        return messages.count()

    def get(self, request, userID, format=None):
        count = self.get_object(userID)
        return Response({
                    'Success': True,
                    'Message': 'Message sent',
                    'Data': {
                        'userID': f"{userID}",
                        'service_type':'All',
                        'Total Messages': f'{count}'
                    }
                }, 200)



class RecipientList(APIView):
    """
    This allows view the list of the Recipients saved by all users.
    """
    # queryset = Message.objects.filter(service_type='IF')
    serializer_class = RecipientSerializer

    def get(self, request, format=None):
        recipient = Recipient.objects.all()
        serializer = RecipientSerializer(recipient, many=True)
        return Response(serializer.data)


class RecipientsForUser(APIView):
    """
    This allows view the list of the Recipients saved by all users.
    """
    # queryset = Message.objects.filter(service_type='IF')
    serializer_class = RecipientSerializer

    def get(self, request, userID, format=None):
        recipients = Recipient.objects.filter(userID=userID)
        if recipients.exists():
            if request.data is None:
                return Response({"Success": True, "Message": "No Recipients For User", "Data": [request.data], 'status': status.HTTP_204_NO_CONTENT})
            else:
                serializer = RecipientSerializer(recipients, many=True)
                return Response({"Success": True, "Message": "Recipients Retrieved", "Data":serializer.data, 'status': status.HTTP_200_OK})
        else:
            return Response({"Failure": True, "Message": "User Does not exist", "Data": [], 'status': status.HTTP_400_BAD_REQUEST})


class RecipientCreate(generics.CreateAPIView):
    '''
    This Endpoints creates a new recipient just like one would add a contact on his phone.
    The catch is have a PhoneBook system of sorts. Since the system will have multiple users,
    Each user can save a number once but multiple numbers. A number can also be in multiple user PhoneBook

    Format is to be in:
    {'recipientName':<the contact name>, 'recipientNumber':<the contacts number>, 'userid':'The user who wants to save the contact'}
    '''
    queryset = Recipient.objects.all()
    serializer_class = RecipientSerializer

    def post(self, request, *args, **kwargs):
        recipientNumber = request.data.get("recipientNumber")
        userID = request.data.get("userID")
        queryset = Recipient.objects.filter(
            userID=userID).filter(recipientNumber=recipientNumber)

        if queryset.exists():
            return Response({"Failure": True, "Message": "This User Already Has This Phone number saved", "Data": [], 'status': status.HTTP_400_BAD_REQUEST})
        else:
            self.create(request, *args, **kwargs)
            return Response({"Success": True, "Message": "Recipient created", "Data": [request.data], 'status': status.HTTP_201_CREATED})


# This is the function for updating and deleting each recipient in a list
class RecipientDetail(views.APIView):
    """
    Update or delete a recipient instance.
    """

    def get_object(self, recipientNumber):
        try:
            return Recipient.objects.filter(recipientNumber=recipientNumber)
        except Recipient.DoesNotExist:
            return Response({"Failure": True, "Message": "This number is not saved", "Data": [], 'status': status.HTTP_400_BAD_REQUEST})
    """
    This Updates the information of the added recipient
    """

    def put(self, request, recipientNumber, format=None):
        recipient = self.get_object(recipientNumber)
        serializer = RecipientSerializer(recipient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    """
    This Deletes the information of the added recipient
    """

    def delete(self, request, recipientNumber, format=None):
        recipient = self.get_object(recipientNumber)
        recipient.delete()
        return Response({"Item": "Successfully Deleted"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_receipents_details(request):
    print(request.data)
    if request.method == 'POST':
        data = request.data
        serializer = RecipientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


@api_view(['PUT'])
def save_recipients_details(request):
    """
      Here we are going to save the recipient details such as email and phone number
      based on his recipient name(making sure all usernames are unique)
      """
    if request.method == 'PUT':
        try:
            Receipent.objects.filter(name=request.data['name']).update(email=request.data['email'],
                                                                       phone_number=request.data['phone_number'])
            receipent = Receipent.objects.get(name=request.data['name'])
            receipentData = RecipientSerializer(receipent, many=False).data
            data = {
                'message': 'Updated successfully',
                'data': receipentData,
                "status": status.HTTP_200_OK
            }
            return JsonResponse(data, status=status.HTTP_200_OK)
        except:
            return JsonResponse({"error": "There is no recipient with this name"}, status=status.HTTP_200_OK)


@api_view(['GET'])
def sms_list(request):
    """
    This view will retrieve every message sent by all customer in twillo.
    """
    if request.method == 'GET':
        # Connect to Twilio and Authenticate
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN)
        try:
            # Pull information from Twilio
            messages = client.messages.list(limit=10)
            sms = []
            for record in messages:
                message = {
                    "content": record.body,
                    "account_sid": record.sid,
                    "receiver": record.to,
                    "date_created": record.date_created,
                    "price": record.price,
                    "status": record.status
                }
                # append to the sms list.
                sms.append(message)
            return JsonResponse({"Success": status.HTTP_200_OK, "Message": "Message Sent", "Data": sms})
            # return JsonResponse(sms, status=200, safe=False)
        except TwilioRestException as e:
            return JsonResponse({"e": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SmsHistoryList(generics.ListAPIView):
    """
    This is used to pull sms history on database
    The senderID should be added at endpoint 
    /v1/sms/sms_history/<senderID>
    """
    serializer_class = MessageSerializer

    def get_queryset(self):
        senderID = self.kwargs["senderID"]
        return Message.objects.filter(senderID=senderID)


class SmsHistoryDetail(generics.RetrieveAPIView):
    """
    Call a particular History of user with users senderID
    """
    serializer = MessageSerializer

    def get_queryset(self):
        pk = self.kwargs["pk"]
        return Message.objects.get(pk=pk)

    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)


def translateMessages(request):
    if request.method == 'GET':
        """
        Translates multiple messages in a single go to the specified language
        Need to send message and language(the language you want to translate) 
        Set of languages supported are 
        The destination here must be a key of the below dictionary(eg:af)
        {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
    'fil': 'Filipino',
    'he': 'Hebrew'
}
        """
        if request.query_params.get('language') is None:
            return JsonResponse({"error": "Enter the language you want to translate"},
                                status=status.HTTP_400_BAD_REQUEST)
        if len(request.GET.getlist('message')) == 0:
            return JsonResponse({"error": "Enter message"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            messages = request.GET.getlist('message')
            language = request.query_params.get('language')
            # Customizing service URL We can use another google translate domain for translation. If multiple URLs
            # are provided it then randomly chooses a domain.
            translator = Translator(service_urls=[
                'translate.google.com',
                'translate.google.co.kr',
            ])
            translations = translator.translate(messages, dest=language)
            result = []
            for translation in translations:
                result.append({
                    'original text': translation.origin,
                    'translated text': translation.text
                })
            return JsonResponse({"message": "Translated all the texts successfully", "data": result},
                                status=status.HTTP_200_OK)
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_400_BAD_REQUEST)



def get_numbers_from_group(request, groupID):
    group = get_object_or_404(Group, groupID=groupID)
    group_numbers =[val.phoneNumbers for val in group.numbers.all()]
    print(group_numbers)
    return group_numbers


# GROUP VIEWS
# This is the function for Listing and creating A GroupList

class GroupBySenderList(generics.ListAPIView):
    """
    This allows view the list of the groups created by a user.

    """
    serializer_class = GroupSerializer

    def list(self, request, **kwargs):
        senderID = self.kwargs["senderID"]
        queryset = Group.objects.filter(senderID=senderID)
        serializer = GroupSerializer(queryset, many=True)
        return Response({"Success": status.HTTP_200_OK, "Message": f"Groups Created by {senderID}", "Group-Info": serializer.data})
        # return Response(serializer.data)


class GroupList(generics.ListAPIView):
    """
    This allows view the list of the groups available on DB.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = GroupSerializer(queryset, many=True)
        return Response({"Success": status.HTTP_200_OK, "Message": "Groups Available", "Group-Info": serializer.data})


class GroupCreate(generics.CreateAPIView):
    """
    This allows users add the recipient's numbers to the new group and create a group.
    Maximum character is 20000
    format follow {"groupName":"", "senderID":""}

    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def post(self, request, *args, **kwargs):
        groupName = request.data.get("groupName")
        senderID = request.data.get("senderID")
        try:
            get_object_or_404(Sender, senderID=senderID)
            queryset = Group.objects.filter(senderID=senderID, groupName=groupName)

            if senderID == "string" or senderID == None:
                return Response({"Failure": status.HTTP_400_BAD_REQUEST, "Message": "String is empty", "Data": {"userID": "string is empty"}})
            if groupName == "string" or groupName == None:
                return Response({"Failure": status.HTTP_400_BAD_REQUEST, "Message": "String is empty", "Data": {"groupName": "empty"}})
            if queryset.exists():
                return Response({"This group exists and it has same user, please specify another group with or change the senderID"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # self.create(request, *args, **kwargs)
                serializer = GroupSerializer(data=request.data)
                if serializer.is_valid():
                    value = serializer.save()
                    groupID = value.groupID
                    value.save()
                    return Response({"Success": "True", "status": status.HTTP_201_CREATED, "Message": "Group Created", "Data": request.data, "groupID": groupID})
                return Response({"Failure": status.HTTP_400_BAD_REQUEST, "Message": "Bad Request", "Data": serializer.errors})
        except:
            return Response({"Failure": status.HTTP_400_BAD_REQUEST, "Message": "Bad Request", "Data": serializer.errors})

# This is the function for updating and deleting each recipient in a list


class GroupDetail(views.APIView):
    """
    The groupName is required to delete the group and userID is required alongside the groupName to update.\n
    To update simply use: /v1/sms/group_update/nameOfGroup...then in body enter {"groupName":"updatedgroupName", "userID":""}.\n
    To delete simply use: /v1/sms/group_update/groupName
    """

    def get_object(self, pk):
        try:
            return Group.objects.get(groupName=pk)
        except Group.DoesNotExist:
            return Response({"Item": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    """
    This Updates the information of the added recipient
    """

    def put(self, request, pk, format=None):
        group = self.get_object(pk)
        serializer = GroupSerializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"Success": "True", "status": status.HTTP_200_OK, "Message": "GroupName Updated", "Data": serializer.data})
        return Response({"Error": status.HTTP_400_BAD_REQUEST, "Message": "GroupDetails Not Found", "Numbers": serializer.errors})


class GroupDelete(generics.DestroyAPIView):
    """
    To delete simply use: /v1/sms/group_update/groupName
    """

    def get_object(self, groupname):
        number = get_object_or_404(Group, groupName=groupname)
        return number

    def delete(self, request, groupname, format=None):
        group = self.get_object(groupname)
        group.delete()
        return Response({"Item": "Successfully Deleted"}, status=status.HTTP_200_OK)


class GroupNumbersList(APIView):
    """
    The user can List all numbers in a group, or create a new group.
    """

    def get(self, request, format=None):
        groupNumber = GroupNumbers.objects.all()
        serializer = GroupNumbersSerializer(groupNumber, many=True)
        return Response({"Success": "True", "status": status.HTTP_200_OK, "Message": "PhoneNumbers Available", "Numbers": serializer.data})


class GroupNumbersBySenderList(APIView):
    """
    The user can List all numbers in a specific group. This requires  {"userID":""}
    """

    def get(self, request, groupname, format=None):
        if ValueError:
            return Response({"Success": False, "Message": "Failed Request", "Data": "String UserID needed", 'status': status.HTTP_400_BAD_REQUEST})
        # groupNumber = GroupNumbers.objects.filter(group__groupName=groupname)
        groupNumber = get_object_or_404(GroupNumbers, group__groupName=groupname)
        serializer = GroupNumbersSerializer(groupNumber, many=True)
        return Response({"Success": "True", "status": status.HTTP_200_OK, "Message": f"PhoneNumbers Available to {groupname}", "Numbers": serializer.data})


class GroupNumbersCreate(generics.CreateAPIView):
    """
    The user create all numbers and add to group, or create a new group.
    Group is an instance...so the ID of the group is to be passed in.
    It requires the ID of the already created group.
    Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.
    Format is as follows:
    {"groupID":"<UUID given upon creating a group>", "phoneNumbers":"<a phone number>"}
    Numbers must be seperated by only a comma, no spaces
    """
    queryset = GroupNumbers.objects.all()
    serializer_class = GroupNumbersPrimarySerializer

    def post(self, request, *args, **kwargs):
        duplicates = []
        groupID = request.data.get("groupID")
        phoneNumbers = request.data.get("phoneNumbers")

        
        group = get_object_or_404(Group, groupID=groupID)
        for number in phoneNumbers.split(","):
            queryset = GroupNumbers.objects.filter(
                group=group, phoneNumbers=number)
            if queryset.exists():
                duplicates.append(f"{number} already exists in this group")
            else:
                # self.create(request, *args, **kwargs)
                request.POST._mutable = True 
                request.data["group"] = group.id
                request.data["phoneNumbers"] = number
                serializer = GroupNumbersPrimarySerializer(data=request.data)
                
                if serializer.is_valid():
                    serializer.save()
                               
            
        request.data["phoneNumbers"] = phoneNumbers
        request.POST._mutable = False 
        # request.data._mutable = False
        return Response(
                {
                    "Success": "True", 
                    "status": status.HTTP_201_CREATED, 
                    "Message": f"PhoneNumbers added to  group with Instance of {groupID}", 
                    "Number": request.data, "duplicates":duplicates})


class GroupNumbersDetail(APIView):

    """
    The user can delete a phoneNumber instance.
    """
    # def get_object(self, pk):
    # try:
    #     return Group.objects.get(groupName=pk)
    # except Group.DoesNotExist:
    #     raise Http404

    def get_object(self, pk):
        number = get_object_or_404(GroupNumbers, pk=pk)
        return number

    def delete(self, request, pk, format=None):
        groupNumber = self.get_object(pk=pk)
        groupNumber.delete()
        return Response({"Item": "Successfully Deleted"}, status=status.HTTP_204_OK)


@api_view(["PUT"])
def update_group_number(request, pk):
    """
    The user can Retrieve, update or delete a phoneNumber instance.\n\n
    In Postman: v1/sms/group_recipient_update/phoneNumber(pk)
    This takes in this format: {"group": "instance of group", "phoneNumber": ""}
    """
    try:
        groupnumber = GroupNumbers.objects.get(pk=pk)
    except GroupNumbers.DoesNotExist:
        return Response({"Item": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({"Error": f"{str(e)}"})

    if request.method == 'PUT':
        data = request.data
        serializer = GroupNumbersSerializer(groupnumber, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"Success": status.HTTP_202_ACCEPTED, "Message": "PhoneNumber updated", "Number": serializer.data})
        return Response({"Error": status.HTTP_400_BAD_REQUEST, "Message": "Bad Request", "Number": serializer.errors})
        # return JsonResponse(serializer.errors, status=400)

# @api_view(['POST'])
# def send_with_infobip(request):
#     # message = request.data['message']
#     # recipients = Receipent.objects.filter()
#     # serializer = RecipientSerializer(data=recipients,many=True)
#     # serializer.is_valid()
#     # info = serializer.data
#     # response = json.dumps(info)
#     data = {
#         "from": "InfoSMS",
#         "to": "+2347069501730",
#         "text": "Hello we are testing the service"
#     }
#     headers = {'Authorization': '32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b'}
#     r = requests.post("https://jdd8zk.api.infobip.com", data=data,headers=headers)
#     response = r.status_code
#     return JsonResponse(response,safe=False)
# INFOBIP MESSAGING VIEWS


class InfobipSendMessage(generics.CreateAPIView):
    """
    This is to send a single SMS to a user using Infobip. Format is to be in
    {"senderID":"", "content":"", "receiver":""}
    where senderID is the userID, content is the message 
    and the receiver is the number to be sent to in the format '2348038888888'
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def post(self, request, *args, **kwargs):
        receiver = request.data["receiver"]
        text = request.data["content"]
        sender = request.data["senderID"]
        request.data["service_type"] = "IF"
        serializer = MessageSerializer(data=request.data)
        conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
        payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (sender, receiver, text)
        if serializer.is_valid():
            value = serializer.save()
            data = {
                "from": sender,
                "to": receiver,
                "text": text
            }
            headers = {
                'Authorization': 'App {"32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b"}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
                }
            # r = requests.post("https://jdd8zk.api.infobip.com",
            #                   data=payload, headers=headers)
            # response = r.json()
            value.service_type = 'IF'
            value.messageStatus = 'P'
            conn.request("POST", "/sms/2/text/advanced", payload, headers)
            res = conn.getresponse()
            data = res.read().decode('utf-8')
            data = json.loads(data)
            if res.status == 200:
                value.save()
            return JsonResponse({"status": res.status, "message": "", "Data": data})
            # print(data)
        else:
            return Response({"message": "Not Valid"})
        


class InfobipSendMessage2(generics.CreateAPIView):
    """
    This is to send a single SMS to a user using Infobip. 

    This is a Trial Account, the following defaults must hold for a message to be sent succesfully
    1. The sender must be the Default Sender on the account which has been set to 'Phil Trial'
    2. The number to be sent to must be verified number on the account which is '254741628438'

    Format is to be in
    {"senderID":"", "content":"", "receiver":""}
    where senderID is the userID, content is the message 
    and the receiver is the number to be sent to in the format '254741628438'
    """
    serializer_class = MessageSerializer

    def post(self, request):
        receiver = request.data["receiver"]
        text = request.data["content"]
        sender = request.data["senderID"]
        conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")

        # here i tried to break the payload into bits to try dynamic variables
        dest1 = {'to': receiver}
        destination = {'destinations': dest1}
        flash = {'flash': 'true'}
        text = {'text': text}
        sender = {'from': sender}
        array = [sender, destination, text, flash]
        # print(array)

        # this is the sample payload as it from the documentation
        payload = "'messages':[{'from':'%s','destinations':[{'to':'%s'}],'text':'%s','flash':'true'}]" % (
            sender, receiver, text)
        print(payload)
        print('Hello')

        payload3 = {'messages': []}
        this = "{'from':'%s', 'destinations':[{'to':'%s'}], 'text':'%s', 'flash':'true'}" % (
            sender, receiver, text)
        payload3['messages'].append(this)
        print(str(payload3))
        print('hi')
        print(payload3)

        # this is 'appended' payload that was broken into bits
        payload2 = {"messages": array}

        # the rest of the connection codes
        headers = {
            'Authorization': 'App {"32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b"}'
        }
        conn.request("POST", "/sms/2/text/advanced", str(payload3), headers)
        res = conn.getresponse()
        # print(res.msg)
        data = res.read().decode('utf-8')
        data = data.replace('/', '')
        # print(data)
        return JsonResponse({"Status": res.status, "Message": "", "Data": data})

        # if res.status == 200:
        #     # resp = JsonResponse({"Success":res.status, "Message":"Message Sent", "Data":data.decode("utf-8")})
        #     return JsonResponse({"Success":res.status, "Message":"Message Sent", "Data":data.decode("utf-8")})
        # else:
        #     return JsonResponse({"Failure":res.status, "Message":"Message Not Sent", "Data":data.decode("utf-8")})

# class InfobipGroupMessage(generics.CreateAPIView):
#     """
#     This is to send a single SMS to a user using Infobip. Format is to be in
#     {"senderID":"", "content":"", "receiver":""}
#     where senderID is the userID, content is the message
#     and the receiver is the groupid'
#     """
#     # queryset = Message.objects.all()
#     serializer_class= MessageSerializer

#     def post(self, request, *args, **kwargs):
#         msgstatus = []
#         groupPK = request.data["groupPK"]
#         text = request.data["content"]
#         sender = request.data["senderID"]
#         numbers = get_numbers_from_group(request, groupPK)
#         serializer = MessageSerializer(data=request.data)
#         conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
#          for number in numbers:   
#              payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (sender, receiver, text)
#              if serializer.is_valid():
#                  value = serializer.save()
#                  data = {
#                      "from": sender,
#                      "to": receiver,
#                      "text": text
#                    }
#                   headers = {
#                      'Authorization': 'App {"32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b"}',
#                      'Content-Type': 'application/json',
#                       'Accept': 'application/json'
#                       }
#                   r = requests.post("https://jdd8zk.api.infobip.com",
#                                     data=payload, headers=headers)
#                   response = r.json()
#                   value.service_type = 'IF'
#                   conn.request("POST", "/sms/2/text/advanced", payload, headers)
#                   res = conn.getresponse()
#                   data = res.read().decode('utf-8')
#                   data = json.loads(data)
#                   if res.status == 200:
#                       value.save()
#                   print(data)
#                 return JsonResponse({"Status": res.status, "Message": "", "Data": data})"""       
#              else:
#                 msgstatus.append(f"something went wrong while sending to {number}")
#         return JsonResponse(response,safe=False)


class InfobipSingleMessage(generics.RetrieveAPIView):
    """
    This enpoint will retreive a all sms sent through twillo by a distinct sender. Format is to be in
    {"senderID":""}
    where senderID is the userID of the sender you wish to view all infobip sent sms,
    """
    # def get_object(self, senderID):
    #     try:
    #         Message.objects.filter(service_type='IF').filter(senderID=senderID)
    #     except Message.DoesNotExist:
    #         raise Http404

    def get(self, request, senderID, format=None):
        message = Message.objects.filter(
            service_type='IF').filter(senderID=senderID)
        serializer = MessageSerializer(message, many=True)
        if message:
            return JsonResponse({"Success": status.HTTP_200_OK, "Message": "Messages retrieved", "Data": serializer.data})
        else:
            return JsonResponse({"Success": status.HTTP_204_NO_CONTENT, "Message": "NO Message from this sender", "Data": serializer.data})


class InfobipMessageList(APIView):
    """
    This allows view the list of the Infobip Messages Sent by all users.
    """
    # queryset = Message.objects.filter(service_type='IF')
    serializer_class = MessageSerializer

    def get(self, request, format=None):
        messages = Message.objects.filter(service_type='IF')
        serializer = MessageSerializer(messages, many=True)
        return JsonResponse({"Success": status.HTTP_200_OK, "Message": "Messages retrieved", "Data": serializer.data})


class TwilioSendSms(views.APIView):
    """
    This is to send a single SMS to a user. Format is to be in
    {"receiver":"", 'senderID':"", "content":""}
    where content is the message, senderID is the userID 
    and the phone is the number to be sent to
    """

    def post(self, request):
        receiver = request.data["receiver"]
        content = request.data["content"]

        request.data["service_type"] = "TW"
        serializer_message = MessageSerializer(data=request.data)

        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN)
        if serializer_message.is_valid():
            try:
                value = serializer_message.save()
                message = client.messages.create(
                    from_=settings.TWILIO_NUMBER,
                    to=receiver,
                    body=content
                )
                value.messageStatus = "S"
                value.save()
                return Response({
                    'success': 'true',
                    'message': 'Message sent',
                    'data': {
                        'receiver': f"{receiver}",
                        # 'userID': f"{senderID}",
                        'service_type': 'TWILIO',
                    }
                }, 200)

            except TwilioRestException as e:
                value.messageStatus = "F"
                value.save()
                # return Response({f"{receiver} can't be sent to, review number": str(e)},status=status.HTTP_400_BAD_REQUEST)
                return Response({
                    'success': 'false',
                    'message': 'Message not sent',
                    'error': {
                        # 'userID': f"{senderID}",
                        'recipient': f"{receiver}",
                        'service_type': 'TWILIO',
                        'statusCode': '400',
                        'details': 'Receiver does not exist or Invalid senderID'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'success': 'false',
                'message': 'Message cannot be sent',
                'error': {
                    # 'userID': f"{senderID}",
                    'recipient': f"{receiver}",
                    'service_type': 'TWILIO',
                    'statusCode': '400',
                    'details': 'All fields are required, a field is ommitted'
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class TeleSignSingleSms(generics.CreateAPIView):
    """
    This is endpoint will send a single SMS to a user.
    It was tested with the redoc swagger or openapi.
    Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.
    Format is to be in
    {"receiver":"", 'senderID':"", "content":""}
    where content is the message, senderID is the userID 
    and the receiver is the phone number to be sent to

    But since we are working with a trial account, sms will only be delivered to the registered account, and the sender will be the default account holder
    """
    serializer_class = MessageSerializer

    def post(self, request):
        receiver = request.data["receiver"]
        # print(receiver)
        content = request.data["content"]
        dateScheduled = request.data["dateScheduled"]
        sender = request.data["senderID"]
        request.data["service_type"] = "TS"
        serializer = MessageSerializer(data=request.data)
        # print(serializer)

        # api_key = settings.TELESIGN_API
        # customer_id = settings.TELESIGN_CUST

        if serializer.is_valid():

            mydata = {
                    'receiver':receiver,
                    'text':content,
                    'sender':sender
                    }
            message = Message.objects.create(
                receiver=receiver,
                senderID=sender,
                content=content,
                service_type="TS",
                dateScheduled=dateScheduled
            )

            #calling model method works,but circular import wont allow update on msg obj
            # message.oneTimeSchedule() 

            #Here we write the schedule fn, to remove circualr imports
            message.save()
            messageID = message.messageID
            print(f'Message is {message}')
            print(f'MessaageID is {messageID}')
            task = singleMessageSchedule.apply_async(args=[mydata, messageID], countdown=30)
            message.scheduleID = task.id


            # periodicTaskScheduler(5,7)


            # task = periodicTaskScheduler.apply_async(args=[5,7], countdown=5)
            # task = singleMessageSchedule.apply_async(args=[mydata], countdown=30)
            # task_id = task.id
        else:
            return Response({"details": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "Success": True,
            "Message": "Message Sending",
            "Data": 'response',
            "Msg Recall ID": task.id,
            "Service_Type": "TELESIGN"})


class TeleSignMessageList(APIView):
    """
    This view will list the Telesign Messages Sent by all users.
    """
    # queryset = Message.objects.filter(service_type='IF')
    serializer_class = MessageSerializer

    def get(self, request, format=None):
        messages = Message.objects.filter(service_type='TS')
        serializer = MessageSerializer(messages, many=True)
        return JsonResponse({
            "Success": status.HTTP_200_OK,
            "Message": "Messages retrieved",
            "Data": serializer.data,
            "Service_Type": "TELESIGN"})


# class TeleSignTransactionID1(generics.ListAPIView):
#     """
#     This allows view the list of the Infobip Messages Sent by all users.
#     Format is to be in
#     {'transactionID':'<a valid transaction id>'}
#     """
#     serializer_class = MessageSerializer

#     def get_queryset(self, request, *args, **kwargs):
#         transactionID = self.kwargs["transactionID"]
#         uuid_regex = re.complie(
#             '[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}')
#         if uuid_regex.match(transactionID):
#             message = get_object_or_404(Message, transactionID=transactionID)
#             if message:
#                 return Response({"Success": True, "Message": "Transaction Retrieved", "Data": [request.data], 'status': status.HTTP_302_FOUND})
#             else:
#                 return Response({"Success": False, "Message": "Transaction Failed", "Data": [request.data], 'status': status.HTTP_400_BAD_REQUEST})
#         else:
#             raise ValidationError(
#                 'Please enter a proper uuid field, with 32 charcters')


# class TeleSignTransactionID2(APIView):
#     """
#     This allows view the list of the Infobip Messages Sent by all users.
#     Format is to be in
#     {'transactionID':'<a valid transaction id>'}
#     """
#     # queryset = Message.objects.filter(service_type='IF')
#     serializer_class = MessageSerializer

#     def get(self, request, transactionID, format=None):
#         uuid_regex = re.compile(
#             '[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}')
#         if uuid_regex.match(transactionID) is False:
#             return Response({"Success": False, "Message": "Transaction Failed", "Data": "UUID needed", 'status': status.HTTP_400_BAD_REQUEST})
#         else:
#             transaction = get_object_or_404(
#                 Message, transactionID=transactionID)
#             serializer_message = MessageSerializer(
#                 transaction, many=True, raise_exception=True)
#             return Response({"Success": True, "Message": "Transaction Retrieved", "Data": serializer_message.data, 'status': status.HTTP_302_FOUND})


class TeleSignTransactionID3(generics.ListAPIView):
    """
    This allows view the list of the groups available on DB.
    """
    # queryset = Message.objects.filter(transactionID=transactionID)
    # serializer_class = MessageSerializer

    def list(self, request, **kwargs):
        transactionID = self.kwargs["transactionID"]
        queryset = Message.objects.filter(transactionID=transactionID)        # message = Message.objects.filter(transactionID=transactionID)
        # if ValueError:
        # return Response({"Success": False, "Message": "Transaction Failed", "Data": "UUID needed", 'status': status.HTTP_400_BAD_REQUEST})
        serializer = MessageSerializer(queryset, many=True)
        return Response({"Success": True, "Message": "Transaction Retrieved", "Data": serializer.data, 'status': status.HTTP_302_FOUND})


def getNumbersFromList(stringOfNumbers):
    stringOfNumbers = stringOfNumbers.split(',')
    number = []
    for num in stringOfNumbers:
        num = num.strip()
        number.append(num)
    number = list(dict.fromkeys(number))
    return number


class TeleSignCollectionSms(generics.CreateAPIView):
    """
    This is endpoint will send a single SMS to a user.
    It was tested with the redoc swagger or openapi.
    Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.
    Format is to be in
    {"receiver":"<different numbers seperated by comma>", 'senderID':"UserID", "content":"Message to send"}
    where content is the message, senderID is the userID 
    and the receiver is the GROUPID you want to send a message to
    
    But since we are working with a trial account, sms will only be delivered to the registered account, and the sender will be the default account holder
    """
    serializer_class= MessageSerializer

    def post(self, request):
        receiver = request.data["receiver"]
        text = request.data["content"]
        senderID = request.data["senderID"]
        request.data["service_type"] = "TS"
        msgstat =[]

        number = getNumbersFromList(receiver)
        print(number)
        for receiver in number:
            api_key = settings.TELESIGN_API
            customer_id = settings.TELESIGN_CUST
            # api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
            # customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
            url = 'https://rest-api.telesign.com/v1/messaging'
            headers = {'Accept' : 'application/json', 'Content-Type' : 'application/x-www-form-urlencoded'}
            data = {'phone_number': receiver, 'message': text, 'message_type': 'ARN'}
            serializer = MessageSerializer(data=request.data)
            token = uuid.uuid4()
            if serializer.is_valid():
                r = requests.post(url, auth=HTTPBasicAuth(customer_id, api_key), data=data, headers=headers)
                response = r.json()
                if response['status']['code'] == 290:
                    print(response['status']['code'])
                    msgstat.append(response)
                    value = serializer.save()
                    value.service_type = 'TS'
                    value.messageStatus = 'S'
                    value.receiver= receiver
                    value.grouptoken= token
                    value.transactionID = response['reference_id']
                    value.save()
                else:
                    print(response['status']['code'])
                    msgstat.append(response)
                    value = serializer.save()
                    value.service_type = 'TS'
                    value.messageStatus = 'F'
                    value.receiver= receiver
                    # value.transactionID = response['reference_id']
                    value.save()
            else:
                return Response({"details":"Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "Success":True, 
            "Message":"Message Sending", 
            "Data":msgstat,
            "Service_Type":"TELESIGN" })


class SendGroupSms(views.APIView):
    """
        Send SMS to multiple recipients. 
        {
        "senderID": "existing senderID",
        "content": "body",
        "receiver": "multiple numbers separated by comma and must start with '+' or '1' or '0' or all three",
        "language": "can be null (google api translation of languages are used...e.g "en" represents 'english')"
        }
    """
    def post(self, request):
        #request senderID from user
        senderID = request.data.get("senderID")
        sender = get_object_or_404(Sender, senderID=senderID)

        #collecting the info of user from the sender table which is linked to sender details table
        account = sender.details.get(default=True)
        sid = account.sid
        token = account.token
        service_type = account.service_name
        verified_no = account.verified_no
        
        #Original Text before translation occurs
        original_txt = []
        #log error
        logger.error("posting to group message")
        
        #messageStatus to return
        msgstatus = []

        #more request data from user
        text = request.data["content"]
        language = request.data["language"]
        receiver = request.data["receiver"]

        #Handling the multiple entry info for user to send to group
        receiver = receiver.split(',')
        numbers = []
        for number in receiver:
            number.strip()
            numbers.append(number) 
        numbers = list(set(numbers))
        #check if it only one number
        if len(numbers) <=1:
            result = {'You need to add more numbers...this is a group feature'}
            msgstatus.append(result)
            return Response(msgstatus)

        logger.error("Infobib")
        grouptoken = uuid.uuid4()
        #INFOBIP
        if (service_type.upper() == "IF") or (service_type.upper() == "INFOBIP"):
            
            for number in numbers:
                msg_dict = {'grouptoken':grouptoken, 'content':text, 'senderID':senderID, 'receiver':number}
                
                serializer = MessageSerializer(data=msg_dict)
                
                if serializer.is_valid():
                    conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
                    value = serializer.save()
                    value.grouptoken = grouptoken
                    if (language != 'en' or language != None or language != " " ):
                        original_txt.append(text)
                        text = translateMsg(text, language)
                        payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (senderID, number, text)
                    else:
                        payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (senderID, number, text)
                    
                    data = {
                        "from": senderID,
                        "to": number,
                        "text": text
                    }
                    headers = {
                        'Authorization': 'App %s' % (token),
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                        }
                    conn.request("POST", "/sms/2/text/advanced", payload, headers)
                    res = conn.getresponse()
                    data = res.read().decode('utf-8')
                    data = json.loads(data)
                    # data = data.replace('/', '')
                    if res.status == 200:
                        value.transactionID = data["messages"][0]["messageId"]
                        if ( data["messages"][0]["status"]["groupId"] == 1):
                            value.messageStatus = "P"
                        if ( data["messages"][0]["status"]["groupId"] == 2):
                            value.messageStatus = "U"
                        if ( data["messages"][0]["status"]["groupId"] == 3):
                            value.messageStatus = "S"
                        if ( data["messages"][0]["status"]["groupId"] == 4):
                            value.messageStatus = "E"
                        if ( data["messages"][0]["status"]["groupId"] == 5):
                            value.messageStatus = "FR"
                        To = data["messages"][0]["to"]
                        IF_MSID =data["messages"][0]["messageId"]
                        description = data["messages"][0]["status"]["description"]
                        result = {"success":"True","status": value.messageStatus, "message": f"{value.content}", "messageID":f"{value.messageID}","groupToken":f"{value.grouptoken}", "data": {"to": To, "msg-id":IF_MSID, "description":description}}
                        msgstatus.append(result)
                        print(msgstatus, number)
                    else:
                        result = {"someting went wrong while sending to this {}, please try again".format(number)}
                        msgstatus.append(result)
                    value.save()
                else:
                    result = {"success":"False","message": f"Please check that this {number} is valid as we cant send to it","status":status.HTTP_400_BAD_REQUEST}
                    msgstatus.append(result)
                    # return Response({
                    #     "Success":"False","Message": f"something went wrong while sending to {number}","status":status.HTTP_400_BAD_REQUEST})
            return Response(msgstatus)

        #TWILIO
        elif (service_type.upper() == "TW") or (service_type.upper() == "TWILIO"):

            client = Client(sid,token)

            for number in numbers:
                msg_dict = {'grouptoken':grouptoken,'content':text, 'senderID':senderID, 'receiver':number}

                serializer = MessageSerializer(data=msg_dict)

                if serializer.is_valid():
                    if (language != 'en' or language != None or language != "" ):
                        original_txt.append(text)
                        text = translateMsg(text, language)
                        payload = {'content': text, "receiver": number,"senderID": senderID, "service_type": "TW"}
                    else:
                        payload = {'content': text, "receiver": number,
                                "senderID": senderID, "service_type": "TW"}
                    
                    value = serializer.save()
                    value.grouptoken = grouptoken
                    try:
                        message = client.messages.create(
                            from_=verified_no,
                            to=number,
                            body=text,
                        )
                        if (message.status == 'sent'):
                            value.messageStatus = "S"
                        elif (message.status == 'queued'):
                            value.messageStatus = "P"
                        elif (message.status == 'failed'):
                            value.messageStatus = "F"
                        elif (message.status == 'delivered'):
                            value.messageStatus = "R"
                        else:
                            value.messageStatus = "U"

                        value.transactionID= message.sid
                        result = {"success":"True","status": value.messageStatus, "message": f"{value.content}", "messageID":f"{value.messageID}","groupToken":f"{value.grouptoken}", "data": {"to": number}}
                        msgstatus.append(result)
                        value.save()

                    except TwilioRestException as e:
                        value.messageStatus = "F"
                        value.transactionID = "500-F"
                        result = {'success': 'False',"status": value.messageStatus, 'message': 'message not sent', "messageID":f"{value.messageID}","groupToken":f"{value.grouptoken}", "data": {'recipient': f"{number}", 'details': 'The Phone Number is Not registered to Twilio', "status":status.HTTP_400_BAD_REQUEST}}
                        msgstatus.append(result)
                        value.save()
                else:
                    result = {"success":"False","message": f"something went wrong while sending to {number}","status":status.HTTP_400_BAD_REQUEST}
                    msgstatus.append(result)
            return Response(msgstatus)

        #TELESIGN 
        elif (service_type.upper() == "TS") or (service_type.upper() == "TELESIGN"):
            for number in numbers:
                msg_dict = {'grouptoken':grouptoken, 'content':text, 'senderID':senderID, 'receiver':number}
                serializer = MessageSerializer(data=msg_dict)


                if serializer.is_valid():
                    api_key = token
                    customer_id = sid
                    url = 'https://rest-api.telesign.com/v1/messaging'
                    headers = {'Accept': 'application/json',
                        'Content-Type': 'application/x-www-form-urlencoded'}

                    value = serializer.save()
                    value.grouptoken = grouptoken
                    if (language != 'en' or language != None or language != "" ):
                        original_txt.append(text)
                        text = translateMsg(text, language)
                        data = {'phone_number': number,
                            'message': text, 'message_type': 'ARN'}
                    else:
                        data = {'phone_number': number,
                            'message': text, 'message_type': 'ARN'}
                    r = requests.post(url, auth=HTTPBasicAuth(customer_id, api_key), data=data, headers=headers)
                    response = r.json()
                    if response['status']['code'] == 290:
                        value.service_type = 'TS'
                        value.messageStatus = 'P'
                        value.transactionID = response['reference_id']
                        result = {'success': 'True',"status": value.messageStatus, 'message': f"{value.content}", "messageID":f"{value.messageID}","GroupToken":f"{value.grouptoken}", "data": {'recipient': f"{number}", 'details': response['status']['description'] , "status":status.HTTP_200_OK}}
                        msgstatus.append(result)
                        value.save()
                    else:
                        value.receiver = number
                        value.transactionID = "500-F"
                        value.service_type = 'TS'
                        value.messageStatus = 'F'
                        result = {"success":"False","status": value.messageStatus, 'message': 'Message not sent', "messageID":f"{value.messageID}","groupToken":f"{value.grouptoken}", "data": {'recipient': f"{number}", 'details': response['status']['description'], "status":status.HTTP_400_BAD_REQUEST}}
                        msgstatus.append(result)
                        value.save()
                else:
                    result = {"success":"False","message": f"something went wrong while sending to {number}","status":status.HTTP_400_BAD_REQUEST}
                    msgstatus.append(result)
            return Response(msgstatus)

        # #MessageBird
        elif (service_type.upper() == 'MB' or service_type.upper() == 'MESSAGEBIRD'):
            for number in numbers:
                msg_dict = {'grouptoken':grouptoken, 'content':text, 'senderID':senderID, 'receiver':number}
                serializer = MessageSerializer(data=msg_dict)

                if serializer.is_valid():
                    logger.error("posting to message in MessageBird")

                    value = serializer.save()                    
                    value.grouptoken = grouptoken

                    Access_key = token
                    client = messagebird.Client(Access_key)

                    value.service_type = 'MB'
                    try:
                        if (language != 'en' or language != None or language != ""):
                            original_txt.append(text)
                            content = translateMsg(text, language)
                            value.language = language
                        else:
                            value.language = "en"
                        message = client.message_create(
                            originator=senderID,
                            recipients=[number],
                            body=content,
                        )
                        # data = json.loads(message)
                        #accessing the response
                        data = message.__dict__
                        item = data['_recipients']['items'][0].__dict__
                        value.messageStatus = 'P'
                        value.transactionID = data['id']
                        if data['gateway'] == 10:
                            value.messageStatus = "F"
                            result = {
                                "success": "false",
                                "status": f"{data['gateway']}",
                                "message": f"{original_txt[0]}",
                                "messageID":f"{value.messageID}",
                                "groupToken":f"{value.grouptoken}",
                                "data": {
                                    "gaID": f"{data['id']}",
                                    "body": f"{data['body']}",
                                    "reference": f"{data['reference']}",
                                    "recipients": f"{item['recipient']}",
                                    "status": f"{item['status']}"
                                },
                                "service_type": "MessageBird"
                            }
                            msgstatus.append(result)

                        elif data['gateway'] == 240:
                            value.messageStatus = "S"
                            result ={
                                "success": "True",
                                "status": f"{data['gateway']}",
                                "message": f"{original_txt[0]}",
                                "messageID":f"{value.messageID}",
                                "groupToken":f"{value.grouptoken}",
                                "data": {
                                    "gaID": f"{data['id']}",
                                    "body": f"{data['body']}",
                                    "reference": f"{data['reference']}",
                                    "recipients": f"{item['recipient']}",
                                    "status": f"{item['status']}"
                                },
                                "service_type": "MessageBird"
                                }
                            msgstatus.append(result)
                    except messagebird.client.ErrorException as e:
                        value.receiver = number
                        value.transactionID = "500-F"
                        value.messageStatus = 'F'
                        errors = []
                        for error in e.errors:
                            errors.append(error)
                        result = {
                            'success': 'False',
                            'message': 'Message not sent',
                            "messageID":f"{value.messageID}",
                            "groupToken":f"{value.grouptoken}",
                            'data': {
                                # 'userID': f"{senderID}",
                                'recipient': f"{number}",
                                'service_type': 'MessageBird',
                                'statusCode': '400',
                                'details': errors
                            },
                         "status":status.HTTP_400_BAD_REQUEST}
                        msgstatus.append(result)
                else:
                    result = {"success":"False","message": f"something went wrong while sending to {number}","status":status.HTTP_400_BAD_REQUEST}
                    msgstatus.append(result)
            return Response(msgstatus)
        
        #GatewayApi
        elif (service_type.upper() == 'GA' or service_type.upper() == 'GATEWAYAPI'):
            for number in numbers:
                msg_dict = {'grouptoken':grouptoken, 'content':text, 'senderID':senderID, 'receiver':number}
                serializer = MessageSerializer(data=msg_dict)

                if serializer.is_valid():
                    logger.error("posting to message in MessageBird")

                    value = serializer.save()                    
                    value.grouptoken = grouptoken
                    value.service_type = "GA"
                    try:   
                        if (language != 'en' or language != None or language != ""):
                                original_txt.append(text)
                                content = translateMsg(text, language)
                                value.language = language
                        else:
                            value.language = "en"
                        
                        key = sid
                        secret = token
                        gwapi = OAuth1Session(key, client_secret=secret)
                        req = {
                            'recipients': [{'msisdn': f'{number}'}],
                            'message': f'{content}',
                            'sender': f'{senderID}',
                        }
                        res = gwapi.post('https://gatewayapi.com/rest/mtsms', json=req)
                        data = res
                        result = {
                            "success": "True",
                            "status": f"{value.messageStatus}",
                            "message": f"{original_txt[0]}",
                            "messageID":f"{value.messageID}",
                            "groupToken":f"{value.grouptoken}",
                            "data": data,
                            "service_type": "GatewayAPi"
                            }
                        msgstatus.append(result)
                        
                    except Exception as e:
                        value.messageStatus = "F"
                        value.transactionID = "500-F"
                        value.language = "en"
                        value.save()
                        result = {
                            'success': 'False',
                            'message': 'Message not sent',
                            "messageID":f"{value.messageID}",
                            "groupToken":f"{value.grouptoken}",
                            'data': {
                                # 'userID': f"{senderID}",
                                'recipient': f"{number}",
                                'service_type': 'MessageBird',
                                'statusCode': '400',
                                'details': errors
                            },
                         "status":status.HTTP_400_BAD_REQUEST}
                        msgstatus.append(result)   
                else:
                    result = {"success":"False","message": f"something went wrong while sending to {number}","status":status.HTTP_400_BAD_REQUEST}
                    msgstatus.append(result)
            return Response(msgstatus)        
    #INVALID SERRVICE
        else:
            return Response({
                "success": "False",
                "details": f"{service_type} not available"}, status=status.HTTP_400_BAD_REQUEST)

class SendFlashSms(views.APIView):
    """
    Send SMS that does not drop in user's inbox. 
    { "senderID" : "your ID", "receiver" : "recipient number", "content" : "your message" }
    """
    serialrizer_class = MessageSerializer
    def post (self, request, *args, **kwargs):
        service_type = request.data["service_type"] 
        
        #INFOBIP
        if (service_type.upper() == "IF") or (service_type.upper() == "INFOBIP"): 
            
            receiver = request.data["receiver"]
            text = request.data["content"]
            sender = request.data["senderID"]
            conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")

            # here i tried to break the payload into bits to try dynamic variables
            dest1 = {'to': receiver}
            destination = {'destinations': dest1}
            flash = {'flash': 'true'}
            text = {'text': text}
            sender = {'from': sender}
            array = [sender, destination, text, flash]
            # print(array)

            # this is the sample payload as it from the documentation
            payload = "'messages':[{'from':'%s','destinations':[{'to':'%s'}],'text':'%s','flash':'true'}]" % (
                sender, receiver, text)
            print(payload)
            print('Hello')

            payload3 = {'messages': []}
            this = "{'from':'%s', 'destinations':[{'to':'%s'}], 'text':'%s', 'flash':'true'}" % (
                sender, receiver, text)
            payload3['messages'].append(this)
            print(str(payload3))
            print('hi')
            print(payload3)

            # this is 'appended' payload that was broken into bits
            payload2 = {"messages": array}

            # the rest of the connection codes
            headers = {
                'Authorization': 'App {"32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b"}'
            }
            conn.request("POST", "/sms/2/text/advanced", str(payload3), headers)
            res = conn.getresponse()
            # print(res.msg)
            data = res.read().decode('utf-8')
            data = data.replace('/', '')
            # print(data)
            return JsonResponse({"Status": res.status, "Message": "Flash sms sent", "Data": payload2})

        elif (service_type.upper() == "TW") or (service_type.upper() == "TWILIO"): 

            msgstatus = []
            text = request.data["text"]
            senderID = request.data["senderID"]
            receiver = request.data["receiver"]

            data = {'content': text, "receiver": receiver,
                                "senderID": senderID, "service_type": "TW", "flash": True}

            serializer_flash = MessageSerializer(data=data)

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            if serializer_flash.is_valid():
                try:
                    client.messages.create(
                        from_=settings.TWILIO_NUMBER,
                        to=receiver,
                        body=text,
                    )
                    data["details"].append(
                        {"to": receiver, "status": "200", "Success": True})
                    value = serializer_flash.save()
                    value.messageStatus = "S"
                    value.save()

                except:
                    data["details"].append(
                        {"to": receiver, "status": "400", "success": False, "error": "Number isn't valid and/or can't be sent to"})
                    value = serializer_flash.save()
                    value.messageStatus = "F"
                    value.save()
            else:
                msgstatus.append(
                    f"something went wrong while sending to {receiver}", status=status.HTTP_400_BAD_REQUEST)
            return Response(msgstatus, status=status.HTTP_200_OK)

#       elif (service_type.upper() == "TS") or (service_type.upper() == "TELESIGN"): 
#            return Response()
        else:
            return Response({
                "Success": False,
                "details": f"{service_type} not available"}, status=status.HTTP_400_BAD_REQUEST)

#NoW REDUNDANT
class TransactionID(APIView):
    """
    This returns the status of a message given a messageID.
    Format {msgID:"your message ID"}
    """
    serializer = MessageSerializer
    def get(self, request, messageID, format=None):
        # dbTransID = Message.objects.get(messageID=transactionid)
        # if dbTransID.exists():
        serializer = MessageSerializer
        try:
            dbTransID = Message.objects.get(messageID=messageID)
            transid = dbTransID.transactionID
            #check if status is not pending and display status
            if dbTransID.messageStatus != "P":
                return Response({"Success": "True", "details": "Transaction status retrieved", "Data": dbTransID.messageStatus, 'status': status.HTTP_200_OK})
            #check serviceType and connect to endpoint
            elif dbTransID.service_type == "TS": #retrieve ID for Telesign
                api_key = settings.TELESIGN_API
                customer_id = settings.TELESIGN_CUST
                url = 'https://rest-api.telesign.com/v1/messaging/'+ transid
                headers = {'Accept' : 'application/json', 'Content-Type' : 'application/x-www-form-urlencoded'}
                payload = ""
                send = requests.request("GET", url, 
                                    auth=HTTPBasicAuth(customer_id, api_key), 
                                    data=payload, 
                                    headers=headers)
                send = send.json()
                testError = send['status']['code']
                failed = [207,210,211,220,221,222.230,231,237,238,250,402,401,400,404,429,502,504,505,506,507,508,509,510,511,512,513,514,515,599]
                if testError == 290 or testError == 291 or testError == 292 or testError == 295:
                    dbTransID.messageStatus = "P"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message is still pending", "Data": send, 'status': status.HTTP_200_OK})
                elif testError == 251 or testError == 500 or testError == 503:
                    dbTransID.messageStatus = "U"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message was not delivered", "Data": send, 'status': status.HTTP_200_OK})
                elif testError == 200 or testError == 202 or  testError == 203:
                    dbTransID.messageStatus = "S"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message was successfully delivered", "Data": send, 'status': status.HTTP_200_OK})
                elif testError in failed:
                    dbTransID.messageStatus = "F"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message sending failed", "Data": send, 'status': status.HTTP_200_OK})
                else:
                    return Response({"Failure": "True", "Message": "Message sending failed", "Data": send, 'status': status.HTTP_200_OK})

            #retrieve ID for infobip
            elif dbTransID.service_type == "IF":
                conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
                url = "/sms/1/reports?messageId=" + transid
                payload = ''
                headers = {
                    'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
                    'Accept': 'application/json'
                }
                conn.request("GET", url, payload, headers)
                res = conn.getresponse()
                data = res.read().decode('utf-8')
                data = json.loads(data)
                testError = data["results"][0]["status"]["groupId"]
                if testError == 1:
                    dbTransID.messageStatus = "P"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message is still pending", "Data": data, 'status': status.HTTP_200_OK})
                elif testError == 2:
                    dbTransID.messageStatus = "U"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message was not delivered", "Data": data, 'status': status.HTTP_200_OK})
                elif testError == 3:
                    dbTransID.messageStatus = "S"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message was successfully delivered", "Data": data, 'status': status.HTTP_200_OK})
                elif testError == 4 or testError == 5:
                    dbTransID.messageStatus = "F"
                    dbTransID.save()
                    return Response({"Success": "True", "Message": "Message sending failed", "Data": data, 'status': status.HTTP_200_OK})
                else:
                    return Response({"Success": "False","Message": "Error retrieving response", "Data": data})

        except ObjectDoesNotExist:
            return Response({"Success": "False", "Message": "TransactionID not found", "Data": [], 'status': status.HTTP_400_BAD_REQUEST})


class GroupTransactionID(APIView):
    """
    This returns the status of a Group message given a groupToken (for group message) or messageID (for single message).
    Format: {"Token":'your group token OR message ID'}
    """
    serializer = MessageSerializer
    def get(self, request, Token, format=None):
        msgResponse = [] #used to store responses
        serializer = MessageSerializer
        try:
            dbTransID = Message.objects.filter(Q(messageID=Token) | Q(transactionID=Token))
            if dbTransID.exists(): 
                for msgID in dbTransID.iterator(): #pick the values in chunks
                    if msgID.messageStatus == "P":
                        # userInfo = SenderDetails.objects.get(msgID.senderID)
                        # api_key = userInfo.token
                        # customer_id = userInfo.sid
                        #Telesign
                        if (msgID.service_type.upper() == "TS"): 
                            api_key = settings.TELESIGN_API
                            customer_id = settings.TELESIGN_CUST
                            url = 'https://rest-api.telesign.com/v1/messaging/'+ msgID.transactionID
                            headers = {'Accept' : 'application/json', 'Content-Type' : 'application/x-www-form-urlencoded'}
                            payload = ""
                            send = requests.request("GET", url, 
                                                auth=HTTPBasicAuth(customer_id, api_key), 
                                                data=payload, 
                                                headers=headers)
                            send = send.json()
                            testError = send['status']['code']
                            failed = [207,210,211,220,221,222.230,231,237,238,250,402,401,400,404,429,500,502,503,504,505,506,507,508,509,510,511,512,513,514,515,599,10008,10009,10010,10011,10012,10013,10014,10015,10017,10019,10020,10030,10032,10033,10034,10036,11000,11001,11003,11004,11005,11009,11010,11011,11017,12000,12009,12017]
                            if testError == 290 or testError == 291 or testError == 292 or testError == 295:
                                msgID.messageStatus = "P"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "P", "Service Message": send, "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            elif testError == 251 or testError == 500 or testError == 503:
                                msgID.messageStatus = "U"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "U", "Service Message": send, "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            elif testError == 200 or testError == 202 or  testError == 203:
                                msgID.messageStatus = "S"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "S", "Service Message": send, "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            elif testError in failed:
                                msgID.messageStatus = "F"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "F", "Service Message": send, "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            else:
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "Error retrieving response", "Service Message": send, "Recipient": msgID.receiver }
                                msgResponse.append(result)

                                #For INFOBIP
                        if (msgID.service_type.upper() == "IF"):
                            # api_key = str(api_key)
                            url = "/sms/1/reports?messageId=" + msgID.transactionID
                            headers = {
                                # 'Authorization': 'App %s' % (api_key),
                                'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
                                'Accept': 'application/json'
                            }
                            payload = ""
                            conn.request("GET", url, payload, headers)
                            res = conn.getresponse()
                            data = res.read().decode('utf-8')
                            data = json.loads(data)
                            testError = data["results"][0]["status"]["groupId"]
                            if testError == 1:
                                msgID.messageStatus = "P"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "P",  "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            elif testError == 2:
                                msgID.messageStatus = "U"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "U", "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            elif testError == 3:
                                msgID.messageStatus = "S"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "S",  "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            elif testError == 4 or testError == 5:
                                msgID.messageStatus = "F"
                                msgID.save()
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "F",  "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                msgResponse.append(result)
                            else:
                                result  = {"Transaction ID": msgID.transactionID, "Message Status": "Error retrieving response", "Service Message": data, "Recipient": msgID.receiver}
                                msgResponse.append(result)
                        #MessageBird
                        if (msgID.service_type.upper() == "MB"):
                                url = "https://rest.messagebird.com/messages?id=" + msgID.transactionID
                                # api_key = str(api_key)
                                headers = {
                                    # 'Authorization': 'AccessKey %s' % (api_key),
                                    # 'Authorization': 'AccessKey ' + api_key,
                                    'Authorization': 'AccessKey 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
                                    'Accept': 'application/json'
                                }
                                client = messagebird.Client(api_key)
                                messages = client.message_list()
                                # testError = messages["_items"][0]["status"]["groupId"]
                                # data = json.loads(data)
                                # testError = data["results"][0]["status"]["groupId"]
                                if testError == 1:
                                    msgID.messageStatus = "P"
                                    msgID.save()
                                    result  = {"Transaction ID": msgID.transactionID, "Message Status": "P",  "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                    msgResponse.append(result)
                                elif testError == 2:
                                    msgID.messageStatus = "U"
                                    msgID.save()
                                    result  = {"Transaction ID": msgID.transactionID, "Message Status": "U", "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                    msgResponse.append(result)
                                elif testError == 3:
                                    msgID.messageStatus = "S"
                                    msgID.save()
                                    result  = {"Transaction ID": msgID.transactionID, "Message Status": "S",  "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                    msgResponse.append(result)
                                elif testError == 4 or testError == 5:
                                    msgID.messageStatus = "F"
                                    msgID.save()
                                    result  = {"Transaction ID": msgID.transactionID, "Message Status": "F",  "Service Message": data["results"][0]["status"], "Recipient": msgID.receiver }
                                    msgResponse.append(result)
                                else:
                                    result  = {"Transaction ID": msgID.transactionID, "Message Status": "Error retrieving response", "Service Message": data, "Recipient": msgID.receiver}
                                    msgResponse.append(result)
                        else:
                            result  = {"Transaction ID": msgID.transactionID, "Message Status": msgID.messageStatus, "Service Message": " ", "Recipient": msgID.receiver }
                            msgResponse.append (result)
                    else:
                        result  = {"Transaction ID": msgID.transactionID, "Message Status": msgID.messageStatus, "Service Message": " ", "Recipient": msgID.receiver }
                        msgResponse.append (result)
                return Response({"Success": "True", "details": "Transaction status retrieved", "Data": {"Service Type": msgID.service_type, "Response": msgResponse }, 'status': status.HTTP_200_OK})
            else:
                return Response({"Error": status.HTTP_400_BAD_REQUEST, "Message": "Token not found", "Token": Token})
        except ObjectDoesNotExist:
            return Response({"Success": "False", "Data": [], 'status': status.HTTP_400_BAD_REQUEST})



class MessageRecall(generics.DestroyAPIView):
    """
    Trying to terminate or recall a message
    """

    def delete(self, request, taskID, format=None):
        celeryTaskapp.control.revoke(taskID)
        return Response({"Item":"Task Successfully Deleted"},status=status.HTTP_200_OK)



# =============================================== SENDER DETAILS ================================================
class SenderRegister(generics.CreateAPIView):
    """ Create a user by simply passing an authorised senderid"""
    serializer_class = SenderSerializer

    def post(self, request, *args, **kwargs):
        sender = request.data.get("senderID")
        serializer = SenderSerializer(data=request.data)
        queryset = Sender.objects.filter(senderID=sender)
        if not queryset.exists():
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({"status":status.HTTP_201_CREATED, "success":"True", "details":"User created"})
            return JsonResponse({"status":status.HTTP_400_BAD_REQUEST, "success":"False", "details":"Improper use of endpoint"})
        else:
            return JsonResponse({"status":status.HTTP_400_BAD_REQUEST, "success":"False", "details":"Sender ID already exists"})
        

class SenderDetailsCreate(generics.CreateAPIView):
    """

    User supplies the given SID and Token provided by the service provider alongside the name of the userID. 
    {"sender":"<ID to associate this credentials with>", "token":"<from SMS gateway>", "sid":"<from SMS gateway>", "service_name":"<TWILIO OR INFOBIP OR MESSAGEBIRD OR TELESIGN OR GATEWAYAPI>"}
    """
    serializer_class = SenderDetailsSerializer

    def post(self, request, *args, **kwargs):
        senderID = request.data.get("sender")
        service_name = request.data.get("service_name")
        user = get_object_or_404(Sender, senderID=senderID)
        senderID = user.senderID
        request.POST._mutable = True
        request.data["sender"] = senderID
        request.POST._mutable = False
        queryset = SenderDetails.objects.filter(senderID=user, service_name=service_name)
        if not queryset.exists():
            serializer = SenderDetailsSerializer(data=request.data)
            if serializer.is_valid():
                value = serializer.save()
                senderID = value.senderID 
                print(senderID)
                details = SenderDetails.objects.filter(senderID=senderID)
                if len(details) != 0:
                    for detail in details:
                        detail.default = False
                        detail.save()
                value.default = True
                value.save()
                return JsonResponse({"status":status.HTTP_201_CREATED, "success":"True", "details":"Details added"}, status=status.HTTP_201_CREATED)
            return JsonResponse({"status":status.HTTP_400_BAD_REQUEST, "success":"False", "details":"Improper use of endpoint"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"status":status.HTTP_400_BAD_REQUEST, "success":"False", "details":f"{service_name} Credentials already exists"}, status=status.HTTP_400_BAD_REQUEST)
        


class SenderDetailsUpdate(generics.UpdateAPIView):
    """

    Users have to specify the given SID and Token supplied by the service provider alongside the name of the senderID
    Format should be {"senderID":"<register User>", "token":"<token>", "sid":"<sid>", "service_name":"<TWILIO OR INFOBIP OR MSG91 OR TELESIGN>"}
    """

    serializer_class = SenderDetailsSerializer

    def put(self, request, *args, **kwargs):
        senderID = request.data.get("sender")
        
        senderID = get_object_or_404(Sender, senderID=senderID)
        service_name = request.data.get("service_name")
        
        senderDetails = get_object_or_404(SenderDetails, senderID=senderID, service_name=service_name)

        serializer = SenderDetailsSerializer(senderDetails, data=request.data)
        print(serializer)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({"status":status.HTTP_202_ACCEPTED, "success":"True", "details":f"{service_name} Credentials updated"}, status=status.HTTP_202_ACCEPTED)
        return JsonResponse({"status":status.HTTP_400_BAD_REQUEST, "success":"False", "details":"Improper use of endpoint"}, status=status.HTTP_400_BAD_REQUEST)

class SenderDetailsList(generics.ListAPIView):
    serializer_class = SenderDetailsSerializer

    def get_queryset(self):
        senderID = self.kwargs["senderID"]
        senderID = get_object_or_404(Sender, senderID=senderID)
        queryset = get_list_or_404(SenderDetails, senderID=senderID)
        return queryset

    
