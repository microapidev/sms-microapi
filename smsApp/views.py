from django.shortcuts import render
from .models import user
from .serializers import userserializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from twilio.rest import Client
from django.conf import settings 
from django.http import HttpResponse


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
    message = ('sample message')
    clients = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    for recipient in serialized_users:
        number = recipient.phone_number
        clients.messages.create(to=recipient,
                                   from_=settings.TWILIO_NUMBER,
                                   body=message)
    return HttpResponse("messages sent!", 200)
