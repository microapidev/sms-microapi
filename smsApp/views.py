import os
import json
import requests
from django.shortcuts import render, get_object_or_404
# from smsApp.models import user
# from smsApp.serializers import UserSerializer
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework import status
from twilio.rest import Client
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse, request
from twilio.base.exceptions import TwilioRestException
import json
import urllib.parse
from urllib.parse import urlencode

# import http.client
# import http
# import mimetypes

# from .infobip import send_single_message_ibp, delivery_reports_ibp
from .models import Receipent, Message, Group
from .serializers import RecepientSerializer, MessageSerializer, GroupSerializer
from googletrans import Translator


# Create your views here.
@api_view(['GET', 'POST'])
# post and get methods on users
def userdetails(request):
    if request.method == 'GET':
        users = user.objects.all()
        serialized_users = UserSerializer(users, many=True)
        return Response(serialized_users.data)
    elif request.method == 'POST':
        serialized_users = UserSerializer(data=request.data)
        if serialized_users.is_valid():
            serialized_users.save()
            return Response(serialized_users.data, status=status.HTTP_201_CREATED)
        return Response(UserSerializer.errors, status=status.HTTP_400_BAD_REQUEST)


# send message to users using twillio
@csrf_exempt
def sendmessage(request):
    for number in serialized_users:
        phone_number = number.phone_number
    message = ('sample message')
    clients = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    for recipient in serialized_users:
        number = recipient.phone_number
        clients.messages.create(to=number,
                                from_=settings.TWILIO_NUMBER,
                                body=message)
    return HttpResponse("messages sent!", 200)


# Create your views here.

class ReceipientList(APIView):
    """
    This allows view the list of the Infobip Messages Sent by all users.
    """
    # queryset = Message.objects.filter(service_type='IF')
    serializer_class= RecepientSerializer

    # def list(self, request):
    #     queryset = self.get_queryset()
    #     serializer = MessageSerializer(queryset, many=True)
    #     return Response(serializer.data)

    def get(self, request, format=None):
        receipents = Receipent.objects.all()
        serializer = RecepientSerializer(receipents, many=True)
        return Response(serializer.data)


class ReceipientCreate(generics.CreateAPIView):
    queryset = Receipent.objects.all()
    serializer_class= RecepientSerializer
    
    def post(self, request, *args, **kwargs):
        recipientNumber = request.data.get("recipientNumber")
        queryset = Receipent.objects.filter(recipientNumber=recipientNumber)
        
        if queryset.exists():
            raise ValidationError('This Id or Number already exists, please enter another number and ID')
        else:
            return self.create(request, *args, **kwargs)


@api_view(['POST'])
def create_receipents_details(request):
    print(request.data)
    if request.method == 'POST':
        data = request.data
        serializer = RecepientSerializer(data=request.data)
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
            receipentData = RecepientSerializer(receipent, many=False).data
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
    This view will retrieve every message sent by customer.
    """
    if request.method == 'GET':
        # Connect to Twilio and Authenticate
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
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
            return JsonResponse(sms, status=200, safe=False)
        except TwilioRestException as e:
            return JsonResponse({"e": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SmsHistoryList(generics.ListAPIView):
    """
    This is used to pull sms history on database
    """
    queryset = Message.objects.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = MessageSerializer(queryset, many=True)
        return Response(serializer.data)


class SmsHistoryDetail(generics.RetrieveAPIView):
    """
    Call a particular History of user with users senderID
    """
    serializer = MessageSerializer
    queryset = Message.objects.all()

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


# nuObjects
@api_view(['POST'])
def nuobj_api(request):
    # users = user.objects.all()
    serializer_class= MessageSerializer
    message = request.data["message"]
    sender = request.data.get("senderID")
    text = request.data.get("content")
    receiver = request.data.get("receiver")
    response = requests.post(f'https://cloud.nuobjects.com/api/send/?user={philemon}&pass={Microapipassword1}&to={receiver}&from={sender}&msg={text}')
    return HttpResponse("Messages Sent!", 200)


# This is the function for Listing and creating A GroupList

class GroupList(generics.ListAPIView):
    """
    This allows view the list of the groups available to a user.
    """
    serializer_class = GroupSerializer

    def get_queryset(self):
        senderID = self.kwargs["senderID"]
        queryset = Group.objects.filter(userID=senderID)
        return queryset



class GroupCreate(generics.CreateAPIView):
    """
    This allows users add the recipient's numbers to the new group and create a group.
    It requires the ID of the already created group Default is "fdbcc88b-6c00-46a8-a639-f5e5de70cef3"
    Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def post(self, request, *args, **kwargs):
        phoneNumbers = request.data.get("phoneNumbers")
        groupName = request.data.get("groupName")
        queryset = Group.objects.filter(phoneNumbers=phoneNumbers, groupName=groupName)

        if queryset.exists():
            raise ValidationError('This Number exists in group, please enter another')
        else:
            return self.create(request, *args, **kwargs)


# This is the function for updating and deleting each recipient in a list
class GroupDetail(views.APIView):
    """
    Update or delete a recipient instance.
    """

    def get_object(self, pk):
        try:
            return Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            raise Http404

    """
    This Updates the information of the added recipient
    """

    def put(self, request, pk, format=None):
        group = self.get_object(pk)
        serializer = GroupSerializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    """
    This Deletes the information of the added recipient
    """

    def delete(self, request, pk, format=None):
        group = self.get_object(pk)
        group.delete()
        return Response({"Item": "Successfully Deleted"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def send_with_infobip(request):
    message = request.data['message']
    # recipients = Receipent.objects.filter()
    # serializer = RecepientSerializer(data=recipients,many=True)
    # serializer.is_valid()
    # info = serializer.data
    # response = json.dumps(info)
    data = {
        "from": "InfoSMS",
        "to": "41793026727",
        "text": message
    }
    headers = {'Authorization': os.getenv("TOKEN")}
    r = requests.post('https://9rr9dr.api.infobip.com/', data=data,headers=headers)
    response = r.status_code
    return JsonResponse(response,safe=False)
        return Response({"Item":"Successfully Deleted"},status=status.HTTP_200_OK)


class NuobjectsMessageList(APIView):
    """
    This allows view the list of the Infobip Messages Sent by all users.
    """
    # queryset = Message.objects.filter(service_type='IF')
    serializer_class= MessageSerializer

    # def list(self, request):
    #     queryset = self.get_queryset()
    #     serializer = MessageSerializer(queryset, many=True)
    #     return Response(serializer.data)

    def get(self, request, format=None):
        messages = Message.objects.filter(service_type='NU')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


# class InfobipSendMessage(generics.CreateAPIView):
#     """
#     This allows users send messages to recipient's.
#     """
#     queryset = Message.objects.all()
#     serializer_class= MessageSerializer
    
#     def post(self, request, *args, **kwargs):
#         sender = request.data.get("senderID")
#         text = request.data.get("content")
#         receiver = request.data.get("receiver")

#         data = send_single_message_ibp(text, receiver)


#         # conn = http.client.HTTPSConnection("jdd8zk.api.infobip.com")
#         # payload = '''{\"messages\":[
#         #                 {\"from\":\"{sender}\",
#         #                 \"destinations\":[{\"to\":\"+2347069501730\"}],
#         #                 \"text\":\"{text}\",
#         #                 \"flash\":true}]}'''
#         # authorization = {'username':'philemonapi', 'password':'Microapipassword1'}
#         # headers = {
#         #     'Authorization': f'{authorization}',
#         #     'Content-Type': 'application/json',
#         #     'Accept': 'application/json'
#         # }

#         # conn.request("POST", "/sms/2/text/advanced", payload, headers)
#         # res = conn.getresponse()
#         # data = res.read()
#         # print(data.decode("utf-8"))
#         return


class InfobipSingleMessage(generics.RetrieveAPIView):
    """
    This allows view a single Infobip Message Sent by a distinct users.
    """
    def get_object(self, senderID):
        try:
            Message.objects.filter(service_type='IF').filter(senderID=senderID)
        except Message.DoesNotExist:
            raise Http404

    def get(self, request, senderID, format=None):
        message = self.get_object(senderID)
        serializer = MessageSerializer(message)
        return JsonResponse(serializer.data)


class NuobjectsSendMessage(generics.CreateAPIView):
    """
    This allows users send messages to recipient's.
    """
    queryset = Message.objects.all()
    serializer_class= MessageSerializer
    
    def post(self, request, *args, **kwargs):
        # message = request.data["message"]
        # sender = request.data.get("senderID")
        # text = request.data.get("content")
        # receiver = request.data.get("receiver")
        # response = requests.post('https://cloud.nuobjects.com/api/credit/?user=philemon&pass=Microapipassword1')
        response = requests.post('https://cloud.nuobjects.com/api/send/?user=philemon&pass=Microapipassword1&to=2347069501730&from=phil&msg=HelloWorld')
        return HttpResponse(response)


class NuobjectsGetBalance(APIView):
    """
    This allows users send messages to recipient's.
    """
    queryset = Message.objects.all()
    serializer_class= MessageSerializer
    
    def get(self, request, format=None):
        messages = Message.objects.filter(service_type='IF')
        # encoded = urlencode(dict(user='philemon', password='Microapipassword1'))
        # url = urllib.parse.quote('https://cloud.nuobjects.com/api/credit/?{encoded}')
        response = requests.post('http://https%3A//cloud.nuobjects.com/api/credit/%3Fuser%3Dphilemon%26pass%3DMicroapipassword1')
        # response = requests.post(f'https://cloud.nuobjects.com/api/send/?user=philemon&pass=Microapipassword1&to=2347069501730&from=phil&msg=HelloWorld')
        return HttpResponse(response)
