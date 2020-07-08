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
from django.http import HttpResponse, Http404
from django.http import JsonResponse
from twilio.base.exceptions import TwilioRestException
import json
import urllib.parse
from urllib.parse import urlencode

# import http.client
# import http
# import mimetypes

# from .infobip import send_single_message_ibp, delivery_reports_ibp
from .models import Receipent, Message, Group, GroupNumbers
from .serializers import RecepientSerializer, MessageSerializer, GroupSerializer, GroupNumbersSerializer 
from googletrans import Translator


# Create your views here.

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


#This is the function for updating and deleting each recipient in a list
class RecipientDetail(views.APIView):
    """
    Update or delete a recipient instance.
    """
    def get_object(self, recipientNumber):
        try:
            return Recipient.objects.get(recipientNumber=recipientNumber)
        except Recipient.DoesNotExist:
            raise Http404
    """
    This Updates the information of the added recipient
    """

    def put(self, request, recipientNumber, format=None):
        recipient = self.get_object(recipientNumber)
        serializer = RecepientSerializer(recipient, data=request.data)
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
        return Response({"Item":"Successfully Deleted"},status=status.HTTP_200_OK)


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
    This view will retrieve every message sent by all customer in twillo.
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
        return  Message.objects.get(pk=pk)

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


# Infobip
# @api_view(['POST'])
# def sendmessage_infobip(request):
#     users = user.objects.all()
#     serialized_users = UserSerializer(users, many=True)
#     message = request.data["message"]
#     for recipient in serialized_users.data:
#         number = recipient.phone_number
#         send_single_message_ibp(message, number)
#     return HttpResponse("Messages Sent!", 200)


# @api_view(['GET'])
# def get_recipients_ibp(request):
#     reports = delivery_reports_ibp()
#     return JsonResponse(reports)


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



def get_numbers_from_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group_numbers = [val.phoneNumbers for val in group.group.all()]
    return group_numbers

@api_view(["POST"])
def send_group_twilio(request):
    """
    Send to an already created group. Format should be {"content":"", "groupID":"", "senderID":"" }
    """
    msgstatus = []
    content = request.data["content"]
    groupPK = request.data["groupPK"]
    senderID = request.data["senderID"]
    numbers = get_numbers_from_group(request, groupPK)


    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    for number in numbers:
        payload = {'content':content, "receiver":number, "senderID":senderID, "service_type":"TW"}
        serializer = MessageSerializer(data=payload)
        if serializer.is_valid():
            try:
                client.messages.create(
                    from_ = settings.TWILIO_NUMBER,
                    to = number,
                    body = content
                )
                msgstatus.append(f"sent to {number}")
                value = serializer.save()
                value.messageStatus = "S"
                value.save()
            except Exception as e:
                msgstatus.append(f"{number} can't be sent to, invalid details")
                value = serializer.save()
                value.messageStatus = "F"
                value.save()
        else:
            msgstatus.append(f"something went wrong while sending to {number}")
    return Response({"details":msgstatus, "service_type":"TWILIO", "senderID":senderID }, status=status.HTTP_200_OK)


#This is the function for Listing and creating A GroupList

class GroupBySenderList(generics.ListAPIView):
    """
    This allows view the list of the groups created by a user.

    """
    serializer_class = GroupSerializer

    def get_queryset(self):
        senderID = self.kwargs["senderID"]
        queryset = Group.objects.filter(userID=senderID)
        return queryset

class GroupList(generics.ListAPIView):
    """
    This allows view the list of the groups available on DB.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = GroupSerializer(queryset, many=True)
        return Response(serializer.data)


class GroupCreate(generics.CreateAPIView):
    """
    This allows users add the recipient's numbers to the new group and create a group.
    format follow {"groupName":"", "userID":""}

    """
    queryset = Group.objects.all()
    serializer_class= GroupSerializer
    
    def post(self, request, *args, **kwargs):
        groupName = request.data.get("groupName")
        senderID = request.data.get("userID")
        queryset = Group.objects.filter(userID=senderID, groupName=groupName)
        
        if senderID == "string" or senderID == None:
            return Response({"userID":"string is empty"},status=status.HTTP_400_BAD_REQUEST)            
        if groupName == "string" or groupName == None:
            return Response({"groupName":"empty"},status=status.HTTP_400_BAD_REQUEST)
        if queryset.exists() :
            return Response({"This group exists and it has same user, please specify another group with or change the senderID"},status=status.HTTP_400_BAD_REQUEST)
        else:
            return self.create(request, *args, **kwargs)


#This is the function for updating and deleting each recipient in a list
class GroupDetail(views.APIView):
    """
    The user can Update or delete a group.
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
        return Response({"Item":"Successfully Deleted"},status=status.HTTP_200_OK)

class GroupNumbersList(APIView):
    """
    The user can List all numbers in a group, or create a new group.
    """
    def get(self, request, format=None):
        groupNumber = GroupNumbers.objects.all()
        serializer = GroupNumbersSerializer(groupNumber, many=True)
        return Response(serializer.data)

class GroupNumbersCreate(generics.CreateAPIView):
    """
    The user create all numbers and add to group, or create a new group.
    Group is an instance...so the ID of the group is to be passed in.
    It requires the ID of the already created group.
    Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.
    Format is as follows:
    {"group":"<unique primarykey given upon creating a group>", "phoneNumbers":"<a phone number>"}
    """
    queryset = GroupNumbers.objects.all()
    serializer_class= GroupNumbersSerializer


    def post(self, request, *args, **kwargs):
        groupID = request.data.get("group")
        phoneNumbers = request.data.get("phoneNumbers")
        queryset = GroupNumbers.objects.filter(group=groupID, phoneNumbers=phoneNumbers)
        
        if queryset.exists() :
            return Response({"This number already exists in this group"},status=status.HTTP_400_BAD_REQUEST)
        else:
            return self.create(request, *args, **kwargs)


class GroupNumbersDetail(APIView):
    """
    The user can Retrieve, update or delete a phoneNumber instance.
    """
    def get_object(self, pk):
        try:
            return GroupNumbers.objects.get(userID=pk)
        except GroupNumbers.DoesNotExist:
            raise Http404
    
    """
    The user can update a phoneNumber instance.
    """

    def put(self, request, pk, format=None):
        groupNumber = self.get_object(pk)
        serializer = GroupNumbersSerializer(groupNumber, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    """
    The user can delete a phoneNumber instance.
    """
    def delete(self, request, pk, format=None):
        groupNumber = self.get_object(pk)
        groupNumber.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(['POST'])
# def send_with_infobip(request):
#     # message = request.data['message']
#     # recipients = Receipent.objects.filter()
#     # serializer = RecepientSerializer(data=recipients,many=True)
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


class InfobipSendMessage(generics.CreateAPIView):
    """
    This is to send a single SMS to a user using Infobip. Format is to be in
    {"senderID":"", "content":"", "receiver":""}
    where senderID is the userID, content is the message 
    and the receiver is the number to be sent to in the format '2348038888888'
    """
    queryset = Message.objects.all()
    serializer_class= MessageSerializer
    
    def post(self, request, *args, **kwargs):
        receiver = request.data["receiver"]
        text = request.data["content"]
        sender = request.data["senderID"]
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            value = serializer.save()
            data = {
            "from": sender,
            "to": receiver,
            "text": text
            }
            headers = {'Authorization': '32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b'}
            r = requests.post("https://jdd8zk.api.infobip.com", data=data,headers=headers)
            response = r.status_code
            value.service_type = 'IF'
            if response == 200:
                value.save()
        return JsonResponse(response,safe=False)


class InfobipGroupMessage(generics.CreateAPIView):
    """
    This is to send a single SMS to a user using Infobip. Format is to be in
    {"senderID":"", "content":"", "receiver":""}
    where senderID is the userID, content is the message 
    and the receiver is the groupid'
    """
    # queryset = Message.objects.all()
    serializer_class= MessageSerializer
    
    def post(self, request, *args, **kwargs):
        msgstatus = []
        groupPK = request.data["groupPK"]
        text = request.data["content"]
        sender = request.data["senderID"]
        numbers = get_numbers_from_group(request, groupPK)
        serializer = MessageSerializer(data=request.data)
        for number in numbers:
            if serializer.is_valid():
                value = serializer.save()
                data = {
                "from": sender,
                "to": number,
                "text": text
                }
                headers = {'Authorization': '32a0fe918d9ce33b532b5de617141e60-a2e949dc-3da9-4715-9450-9d9151e0cf0b'}
                try:
                    r = requests.post("https://jdd8zk.api.infobip.com", data=data,headers=headers)
                    msgstatus.append(f'succesfully sent to {number}')
                    value.messageStatus = "S"
                    value.save()
                except Exception as e:
                    msgstatus.append(f'cant send to the {number}, error: {e}, status: {r}')
                    value.messageStatus = "F"
                    value.save()
                response = r.status_code
                value.service_type = 'IF'
                if response == 200:
                    value.save()
            else:
                msgstatus.append(f"something went wrong while sending to {number}")
        return JsonResponse(response,safe=False)



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
        message = Message.objects.filter(service_type='IF').filter(senderID=senderID)
        serializer = MessageSerializer(message, many=True)
        if message:
            return JsonResponse({"Success":status.HTTP_200_OK, "Message":"Messages retrieved", "Data":serializer.data })
        else:
            return JsonResponse({"Success":status.HTTP_204_NO_CONTENT, "Message":"NO Message from this sender", "Data":serializer.data })


class InfobipMessageList(APIView):
    """
    This allows view the list of the Infobip Messages Sent by all users.
    """
    # queryset = Message.objects.filter(service_type='IF')
    serializer_class= MessageSerializer

    def get(self, request, format=None):
        messages = Message.objects.filter(service_type='IF')
        serializer = MessageSerializer(messages, many=True)
        return JsonResponse({"Success":status.HTTP_200_OK, "Message":"Messages retrieved", "Data":serializer.data })

        
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
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        if serializer_message.is_valid():
            try:
                value = serializer_message.save()
                message = client.messages.create(
                    from_ = settings.TWILIO_NUMBER,
                    to = receiver,
                    body = content
                    )
                value.messageStatus = "S"
                value.save()
                return Response({"details":"Message sent!", "service_type":"TWILIO"}, 200)
            except TwilioRestException as e:
                value.messageStatus = "F"
                value.save()
                return Response({f"{receiver} can't be sent to, review number": str(e)},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"details":"Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
  
