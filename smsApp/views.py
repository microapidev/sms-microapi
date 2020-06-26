from django.shortcuts import render
from smsApp.models import user
from smsApp.serializers import userserializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from twilio.rest import Client
from django.conf import settings 
from django.http import HttpResponse
from django.http import JsonResponse
from twilio.base.exceptions import TwilioRestException
from smsApp.models import Receipent, Message
from smsApp.serializers import RecepientSerializer, MessageSerializer
import json

# Create your views here.
@api_view(['GET','POST'])
#post and get methods on users
def userdetails(request):
    if request.method == 'GET':
        users = user.objects.all()
        serialized_users = userserializer(users, many = True)
        return Response(serialized_users.data)
    elif request.method == 'POST':
        serialized_users = userserializer(data=request.data)
        if serialized_users.is_valid():
            serialized_users.save()
            return Response(serialized_users.data, status=status.HTTP_201_CREATED)
        return Response(userserializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#send message to users using twillio
def sendmessage(request):
    users = user.objects.all()
    serialized_users = userserializer(users, many = True)
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
    This API will retrieve every messages, and a single message sent via Twillo.
    """
    if request.method == 'GET':
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        try:
            messages = client.messages.list(limit=10)
            sms = []
            for record in messages:
                message = {
                    "content" : record.body,
                    "account_sid": record.sid,
                    "receiver" : record.to,
                    "date_created": record.date_created,
                    "price": record.price,
                    "status": record.status
                }
                sms.append(message)
            return JsonResponse(sms, status=200, safe=False)
        except TwilioRestException as e:
            return JsonResponse({"error": "You have not sent SMS"}, str(e), status=status.HTTP_400_BAD_REQUEST)
# client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
# messages = client.messages.list(limit=10)
# for record in messages:
#     print(record.date_created) 