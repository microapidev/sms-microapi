import requests
from requests.auth import HTTPBasicAuth
from django.shortcuts import render, get_object_or_404
from rest_framework.parsers import JSONParser
# from smsApp.models import user
# from smsApp.serializers import UserSerializer
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework import status
from twilio.rest import Client
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse
from django.http import JsonResponse
from twilio.base.exceptions import TwilioRestException
import re
import json
import base64
import http.client
import mimetypes
import urllib.parse
from urllib.parse import urlencode
from .models import Recipient, Message, Group, GroupNumbers
from .serializers import RecipientSerializer, MessageSerializer, GroupSerializer, GroupNumbersSerializer, GroupNumbersPrimarySerializer
from googletrans import Translator
import uuid


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
    This endpoint allows a user to send a single message, while specifying which message provider is to be used.
    To begin user must enter the required info: 
    {
        "senderID" : "",
        "service_type" : "IF or TS or TW",
        "receiver" : "phone number",
        "content" :  "message body"
    }

    IF == Infobip
    TS == Telesign
    TW == Twilio
    """
    
    serializer_class = MessageSerializer

    def post(self, request, *args, **kwargs):
        service_type = request.data.get("service_type")
        senderID = request.data.get("senderID")
        receiver = request.data.get("receiver")
        content = request.data.get("content")
        language = request.data.get("language")
        regex = re.compile(r'^\+?1?\d{9,15}$')
        original_txt = []
        
        if regex.match(receiver):
            
            if (service_type == 'TW'):
                
                message_dict = {'senderID':senderID, 'service_type':service_type, 'receiver':receiver, 'content':content, 'language':language}


                serializer_message = MessageSerializer(data=message_dict)


                client = Client(settings.TWILIO_ACCOUNT_SID,
                                settings.TWILIO_AUTH_TOKEN)
                if serializer_message.is_valid():
                    try:
                        value = serializer_message.save()
                        if (language != 'en' or language != None or language != " " ):
                            original_txt.append(content)
                            content = translateMsg(content, language)
                            
                            message = client.messages.create(
                                from_=settings.TWILIO_NUMBER,
                                to=receiver,
                                body=content
                            )
                        else:
                            message = client.messages.create(
                                from_=settings.TWILIO_NUMBER,
                                to=receiver,
                                body=content
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
                                'message': 'Message sent',
                                'original message': f"{original_txt[0]}",
                                'data': {
                                    'receiver': f"{receiver}",
                                    # 'userID': f"{senderID}",
                                    'message_sent': f"{content}",
                                    'service_type': 'TWILIO',
                                }
                            }, 200)
                        return Response({
                            'success': 'true',
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
                        value.save()
                        return Response({
                            'success': 'false',
                            'message': 'Message not sent',
                            'error': {
                                # 'userID': f"{senderID}",
                                'recipient': f"{receiver}",
                                'twilioError':{"error":f"{str(e)}"},
                                'service_type': 'TWILIO',
                                'statusCode': '400',
                                'details': 'The Phone Number is unregistered to Twilio'
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
            
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

            #Infobip
            elif (service_type == 'IF'):

                message_dict = {'senderID':senderID, 'service_type':service_type, 'receiver':receiver, 'content':content}
                serializer = MessageSerializer(data=message_dict)
                conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
                payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":false}]}" % (senderID, receiver, content)
                # payload =  "{\"messages\":\"[{\"from\":\"{%s}\",\"destinations\":[{\"to\":\"%s\",\"messageId\":\"Stage7-Company\"}],\"text\":\"%s\",\"flash\":false,\"notifyUrl\":\"https://www.example.com/sms/advanced\",\"notifyContentType\":\"application/json\",\"callbackData\":\"DLR callback data\",\"validityPeriod\":720}}" % (senderID, receiver, content)
                # payload = {"from": f"{senderID}", "to":f"{receiver}", "text": f"{content}"}
                if serializer.is_valid():
                    value = serializer.save()
                    if (language != 'en' or language != None or language != ""):
                        original_txt.append(content)
                        content = translateMsg(content, language)
                        data = {
                            "from": senderID,
                            "to": receiver,
                            "text": content
                        }
                        headers = {
                            'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                            }
                    else:
                        data = {
                            "from": senderID,
                            "to": receiver,
                            "text": content
                        }
                        headers = {
                            'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
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
                        value.save()
                    # print(data)
                    if len(original_txt) != 0:
                        return Response({"Status": res.status, "Original Message": f"{original_txt[0]}", "Data": data})
                    return Response({"Status": res.status, "Message": "", "Data": data})
                else:
                    return Response({"message": "Not Valid"})
            
            #For Telesign
            elif (service_type == 'TS'):
                message_dict = {'senderID':senderID, 'service_type':service_type, 'receiver':receiver, 'content':content}
                serializer_message = MessageSerializer(data=message_dict)

                api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
                customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
                url = 'https://rest-api.telesign.com/v1/messaging'

                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'}
                if (language != 'en' or language != None or language != ""):
                    original_txt.append(content)
                    content = translateMsg(content, language)
                    data = {
                        'phone_number': receiver,
                        'message': content,
                        'message_type': 'ARN'
                    }
                else:
                    data = {
                        'phone_number': receiver,
                        'message': content,
                        'message_type': 'ARN'
                    }

                if serializer_message.is_valid():
                    # print(value)
                    # print("break----")
                    r = requests.post(url, 
                                    auth=HTTPBasicAuth(customer_id, api_key), 
                                    data=data, 
                                    headers=headers)
                    value = serializer_message.save()
                    response = r.json()
                    if response['status']['code'] == 290:
                        value.service_type = 'TS'
                        value.messageStatus = 'SC'
                        value.transactionID = response['reference_id']
                        value.save()
                        if len(original_txt) != 0:
                            return Response({
                                "Success": True,
                                "Message": "Message Sending",
                                "Original SMS": f"{original_txt[0]}",
                                "Data": response,
                                "Service_Type": "TELESIGN"
                                })
                        return Response({
                            "Success": True,
                            "Message": "Message Sending",
                            "Data": response,
                            "Service_Type": "TELESIGN"
                            })
                    else:
                        print(response['status']['code'])
                        value = serializer_message.save()
                        value.service_type = 'TS'
                        value.messageStatus = 'F'
                        value.receiver = receiver
                        value.transactionID = "500-F"
                        value.save()
                        return Response({
                            "Success": False,
                            "Message": "Message Couldnt be sent",
                            "Data": response,
                            "Service_Type": "TELESIGN"})
                else:
                    return Response({"details": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({f"Service Type {service_type}": "Not Supported"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({f"{receiver} should be a number starting with +,1,0 ": "Not Supported"}, status=status.HTTP_400_BAD_REQUEST)
    


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
            return Response({"Success": "True", "status": status.HTTP_201_CREATED, "Message": "Group Created", "Data": request.data, "groupID": groupID})

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

    def get(self, request, senderID, format=None):
        if ValueError:
            return Response({"Success": False, "Message": "Failed Request", "Data": "String UserID needed", 'status': status.HTTP_400_BAD_REQUEST})
        groupNumber = GroupNumbers.objects.filter(group__userID=senderID)
        serializer = GroupNumbersSerializer(groupNumber, many=True)
        return Response({"Success": "True", "status": status.HTTP_200_OK, "Message": f"PhoneNumbers Available to {senderID}", "Numbers": serializer.data})


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
                request.data._mutable = True 
                request.data["group"] = group.id
                request.data["phoneNumbers"] = number
                serializer = GroupNumbersPrimarySerializer(data=request.data)
                
                print(serializer)
                if serializer.is_valid():
                    serializer.save()
                    print("yeah")            
            
        request.data["phoneNumbers"] = phoneNumbers
        request.data._mutable = False
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
        return Response({"Item": "Successfully Deleted"}, status=status.HTTP_204_NO_CONTENT)


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
        serializer = GroupNumbersPrimarySerializer(groupnumber, data=data)
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
                'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
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
                value.save()
            # print(data)
        return JsonResponse({"Status": res.status, "Message": "", "Data": data})
        


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
            'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b'
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
#                      'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
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
        translateMessages(content)
        print
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
        print(receiver)
        text = request.data["content"]
        sender = request.data["senderID"]
        request.data["service_type"] = "TS"
        serializer = MessageSerializer(data=request.data)
        # print(serializer)

        # api_key = settings.TELESIGN_API
        # customer_id = settings.TELESIGN_CUST
        api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
        customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
        url = 'https://rest-api.telesign.com/v1/messaging'

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'}

        data = {
            'phone_number': receiver,
            'message': text,
            'message_type': 'ARN'}

        if serializer.is_valid():
            # print(value)
            # print("break----")
            r = requests.post(url, auth=HTTPBasicAuth(
                customer_id, api_key), data=data, headers=headers)
            value = serializer.save()
            response = r.json()
            if response['status']['code'] == 290:
                value.service_type = 'TS'
                value.messageStatus = 'SC'
                value.transactionID = response['reference_id']
                value.save()
                print(value)
            else:
                print(response['status']['code'])
                value = serializer.save()
                value.service_type = 'TS'
                value.messageStatus = 'F'
                value.receiver = receiver
                value.transactionID = uuid.uuid4()
                value.save()
                return Response({
                    "Success": False,
                    "Message": "Message Couldnt be sent",
                    "Data": response,
                    "Service_Type": "TELESIGN"})
        else:
            return Response({"details": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "Success": True,
            "Message": "Message Sending",
            "Data": response,
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
        This endpoint (...v2/sms/send_group_sms) enables group sms using either Twilio, Infobip or Telesign service. 
        The following details are needed in sending a group sms - senderID, groupID, service type and content.
        The groupID is autogenerated upon creating a group, to create a group refer to the endpoint (v1/sms/create_group)
    """
    def post(self, request, *args, **kwargs):
        service_type = request.data["service_type"] 

        #INFOBIP
        if (service_type.upper() == "IF") or (service_type.upper() == "INFOBIP"):
            def post(self, request):
                msgstatus = []
                groupID = request.data["groupID"]
                text = request.data["content"]
                senderID = request.data["senderID"]
                numbers = get_numbers_from_group(request, groupID)

                serializer = MessageSerializer(data=request.data)

                conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
                if not numbers:
                    return Response({"Success": False, "details": "There are no numbers in this group", "SenderID": senderID, "groupID": groupID})
                else:
                    for number in numbers:
                        payload = "{\"messages\":[{\"from\":\"%s\",\"destinations\":[{\"to\":\"%s\"}],\"text\":\"%s\",\"flash\":true}]}" % (senderID, numbers, text)
                        if serializer.is_valid():
                            value = serializer.save()
                            data = {
                                "from": senderID,
                                "to": numbers,
                                "text": text
                            }
                            headers = {
                                'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b',
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                                }
                            value.service_type = 'IF'
                            conn.request("POST", "/sms/2/text/advanced", payload, headers)
                            res = conn.getresponse()
                            data = res.read().decode('utf-8')
                            data = json.loads(data)
                            if res.status == 200:
                                value.save()
                            return Response({"Status": res.status, "Message": "", "Data": data})
                        else:
                            return Response({
                                "Success":False, "Status": 400,
                                "Message": f"something went wrong while sending to {number}"}, status=status.HTTP_400_BAD_REQUEST)
                    return Response({"details": msgstatus, "service_type": "InfoBip", "senderID": senderID}, status=status.HTTP_200_OK)

        #TWILIO
        elif (service_type.upper() == "TW") or (service_type.upper() == "TWILIO"):
            def post(self, request):
                content = request.data["content"]
                groupID = request.data["groupID"]
                senderID = request.data["senderID"]
                numbers = get_numbers_from_group(request, groupID)

                data = {"message": content, "service_type": "TWILIO",
                        "senderID": senderID, 'details': []}
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                if not numbers:
                    return Response({"Success": False, "details": "There are no numbers in this group", "SenderID": senderID, "groupID": groupID})
                else:
                    for number in numbers:
                        payload = {'content': content, "receiver": number,
                                "senderID": senderID, "service_type": "TW"}
                        serializer = MessageSerializer(data=payload)
                        if serializer.is_valid():
                            try:
                                client.messages.create(
                                    from_=settings.TWILIO_NUMBER,
                                    to=number,
                                    body=content
                                )
                                data["details"].append(
                                    {"to": number, "status": "200", "Success": True})
                                value = serializer.save()
                                value.messageStatus = "S"
                                value.save()

                            except:
                                data["details"].append(
                                    {"to": number, "status": "400", "success": False, "error": "Number isn't valid and/or can't be sent to"})
                                value = serializer.save()
                                value.messageStatus = "F"
                                value.save()
                        else:
                            msgstatus.append(
                                f"something went wrong while sending to {number}", status=status.HTTP_400_BAD_REQUEST)
                    return Response(data, status=status.HTTP_200_OK)

        #TELESIGN 
        elif (service_type.upper() == "TS") or (service_type.upper() == "TELESIGN"):

            def post(self, request):
                groupID = request.data["groupID"]
                text = request.data["content"]
                senderID = request.data["senderID"]
                msgstat = []
                numbers = get_numbers_from_group(request, groupID)
                #print(number)
                #grouptoken = uuid.uuid4()
                if not numbers:
                    return Response({"Success": False, "details": "There are no numbers in this group", "SenderID": senderID, "groupID": groupID})
                else:
                    for number in numbers:
                        # api_key = settings.TELESIGN_API
                        # customer_id = settings.TELESIGN_CUST
                        api_key = 'HXwu/7gWs9KMHWilug9NPccJe+nZtUaG6TtfmxikOgQeCP5ErX7uGxIqpufdF2b93Qed9B/WcudRiveDXfaf2Q=='
                        customer_id = 'ACECBD93-21C7-4B8B-9300-33FDEBC27881'
                        url = 'https://rest-api.telesign.com/v1/messaging'
                        headers = {'Accept': 'application/json',
                            'Content-Type': 'application/x-www-form-urlencoded'}
                        data = {'phone_number': number,
                            'message': text, 'message_type': 'ARN'}
                        serializer = MessageSerializer(data=request.data)
                        if serializer.is_valid():
                            try:
                                r = requests.post(url, auth=HTTPBasicAuth(
                                customer_id, api_key), data=data, headers=headers)
                                response = r.json()
                                response['status']['code'] == 290
                                print(response['status']['code'])
                                data["details"].append(
                                        {"to": number, "status": "200", "Success": True})
                                value = serializer.save()
                                value.service_type = 'TS'
                                value.messageStatus = 'S'
                                #value.receiver= receiver
                                #value.transactionID = response['reference_id']
                                #value.grouptoken = grouptoken
                                value.save()
                            except:
                                print(response['status']['code'])
                                data["details"].append(
                                    {"to": number, "status": "400", "success": False, "error": "Number isn't valid and/or can't be sent to"})
                                value = serializer.save()
                                value.service_type = 'TS'
                                value.messageStatus = 'F'
                                #value.receiver = receiver
                                #value.grouptoken = grouptoken
                                # value.transactionID = response['reference_id']
                                value.save()
                        else:
                            return Response({"details": data, "error":"Number isn't valid and/or can't be sent to","service_type": "Telesign", "senderID": senderID}, status=status.HTTP_400_BAD_REQUEST)
                    return Response({
                        "Success":True, 
                        "Message":"Message Sending", 
                        "Data":msgstat,
                        "Service_Type":"TELESIGN" }, status=status.HTTP_200_OK)

        #INVALID SERRVICE
        else:
            return Response({
                "Success": False,
                "details": f"{service_type} not available"}, status=status.HTTP_400_BAD_REQUEST)

class SendGroupSms(views.APIView):
    """
    Flash messages
    """
    serialrizer_class = MessageSerialize
    def post (self, request, *args, **kwargs):
        service_type = request.data["service_type"] 
        
        #INFOBIP
        if (service_type.upper() == "IF") or (service_type.upper() == "INFOBIP"): 

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
                    'Authorization': 'App 32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b'
                }
                conn.request("POST", "/sms/2/text/advanced", str(payload3), headers)
                res = conn.getresponse()
                # print(res.msg)
                data = res.read().decode('utf-8')
                data = data.replace('/', '')
                # print(data)
                return JsonResponse({"Status": res.status, "Message": "", "Data": data})

        elif (service_type.upper() == "TW") or (service_type.upper() == "TWILIO"): 
            
        elif (service_type.upper() == "TS") or (service_type.upper() == "TELESIGN"): 
            
        else:
            return Response({
                "Success": False,
                "details": f"{service_type} not available"}, status=status.HTTP_400_BAD_REQUEST)

class TransactionID(APIView):
    """
    This returns the status of a message given a transactionID or groupToken
    """
    serializer = MessageSerializer
    def get(self, request, msgID, format=None):
        # dbTransID = Message.objects.get(messageID=transactionid)
        # if dbTransID.exists():
        serializer = MessageSerializer
        try:
            dbTransID = Message.objects.get(messageID=msgID)
            transid = dbTransID.transactionID
            #check if status is not pending and display status
            if dbTransID.messageStatus != "P":
                return Response({"Success": True, "Message": "Transaction status retrieved", "Data": dbTransID.messageStatus, 'status': status.HTTP_200_OK})
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
                    return Response({"Success": True, "Message": "Message is still pending", "Data": send, 'status': status.HTTP_200_OK})
                elif testError == 251 or testError == 500 or testError == 503:
                    dbTransID.messageStatus = "U"
                    dbTransID.save()
                    return Response({"Success": True, "Message": "Message was not delivered", "Data": send, 'status': status.HTTP_200_OK})
                elif testError == 200 or testError == 202 or  testError == 203:
                    dbTransID.messageStatus = "S"
                    dbTransID.save()
                    return Response({"Success": True, "Message": "Message was successfully delivered", "Data": send, 'status': status.HTTP_200_OK})
                elif testError in failed:
                    dbTransID.messageStatus = "F"
                    dbTransID.save()
                    return Response({"Success": True, "Message": "Message sending failed", "Data": send, 'status': status.HTTP_200_OK})
                else:
                    return Response({"Message": "Error retrieving response"})

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
                    return Response({"Success": True, "Message": "Message is still pending", "Data": data, 'status': status.HTTP_200_OK})
                elif testError == 2:
                    dbTransID.messageStatus = "U"
                    dbTransID.save()
                    return Response({"Success": True, "Message": "Message was not delivered", "Data": data, 'status': status.HTTP_200_OK})
                elif testError == 3:
                    dbTransID.messageStatus = "S"
                    dbTransID.save()
                    return Response({"Success": True, "Message": "Message was successfully delivered", "Data": data, 'status': status.HTTP_200_OK})
                elif testError == 4 or testError == 5:
                    dbTransID.messageStatus = "F"
                    dbTransID.save()
                    return Response({"Success": True, "Message": "Message sending failed", "Data": data, 'status': status.HTTP_200_OK})
                else:
                    return Response({"Message": "Error retrieving response"})

        except ObjectDoesNotExist:
            return Response({"Failure": True, "Message": "TransactionID not found", "Data": [], 'status': status.HTTP_400_BAD_REQUEST})