import random
import string
import requests
from django.shortcuts import render
from .models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from twilio.rest import Client
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.http import JsonResponse
from twilio.base.exceptions import TwilioRestException
import json
from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.http import Http404
# from .infobip import send_single_message_ibp, delivery_reports_ibp
from .models import Receipent, Message
from .serializers import RecepientSerializer, MessageSerializer, UserSerializer
from googletrans import Translator


# def add_user(request):

class CreateUser(generics.CreateAPIView):

    """
    This allows for User Registration.
    """
    serializer_class = UserSerializer

    def get_object(self, name):
        try:
            return User.objects.get(username=name)
        except User.DoesNotExist:
            raise Http404
 
    def post(self, request):
        otp = "".join(random.choice(string.digits) for i in range(6))
        # request_dict = request.data 
        # request_dict["otp"] = otp 
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user_email = request.data["email"]
            user = User.objects.get(email=user_email)
            user.otp = otp
            user.save()
            print(otp) # print to screen for now, when sms is enabled, then it'd be changed to send as sms
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
class ListUser(generics.ListAPIView):
    """

    Only for admins.   
    Shows the list of users registered on the platform.   
    To test, endpoint - 'user/list', add given token in the key-value format and send a GET request 
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()

"""
For function based views, please add these decorators at the top
@permission_class(["IsAuthenticated"])
@authentication_classes(["TokenAuthentication"])

For class based views, inside the class, add the following 
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

All these are necessary for authentication
"""  

class VerifyAccount(views.APIView):
    """
    Verify phone number using OTP to make account active. This must be done
    before any transaction can occur on the account.
    To verify, visit the endpoint and post email, phoneNumber and otp using those variables as keys

    """
    def post(self, request):
        try:
            otp = request.data["otp"]
            email = request.data["email"]
            phone = request.data["phoneNumber"]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Http404
                
            if user.phoneNumber == phone:
                if user.otp == otp:
                    user.is_active = True
                    user.save()
                    return Response({"details":f"{user.name} is now active"}, status=status.HTTP_202_ACCEPTED)
                return Response({"details":"OTP not valid"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"details":"Credentials not valid"}, status=status.HTTP_400_BAD_REQUEST)
        




# send message to users using twillio
@csrf_exempt
def sendmessage(request):
    users = user.objects.all()
    serialized_users = UserSerializer(users, many=True)
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

@api_view(['GET'])
def get_recipient_details(request):
    """
        List of all recipients
        """
    if request.method == 'GET':
        receipents = Receipent.objects.filter()
        receipentData = RecepientSerializer(receipents, many=True)
        data = {
            'message': 'Retreived token successfully',
            'data': receipentData.data,
            "status": status.HTTP_200_OK
        }
        return JsonResponse(data, status=status.HTTP_200_OK)


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
    users = user.objects.all()
    serialized_users = UserSerializer(users, many=True)
    message = request.data["message"]
    for recipient in serialized_users.data:
        # User and pass (username and password) can be stored in env variables for live testing
        data = {'user': 'demo', 'pass': 'pass', 'to': recipient, 'from': 'Testing', 'msg': message}
        response = requests.post('https://cloud.nuobjects.com/api/send/', data=data)
    return HttpResponse("Messages Sent!", 200)
