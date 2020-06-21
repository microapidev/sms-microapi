from django.shortcuts import render
from .models import user
from .serializers import userserializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from twilio.rest import Client
#from django.conf import settings 
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
    #add twilio sid, auth token and twilio number
    account_sid = ""
    auth_token = ""
    twilio_number = ""
    users = user.objects.all()
    serialized_users = userserializer(users, many = True)
    # for number in serialized_users:
    #     phone_number = number.phone_number
    message = ('Hello world message')
    
    clients = Client(account_sid,auth_token)
    #loop over users in database and obtain their phone numbers and assign them to number variable
    
    for recipient in serialized_users:
        number = recipient.phone_number
    
        clients.messages.create(to=number,
                                   from_= twilio_number,
                                   body=message)
    return HttpResponse("messages sent!", 200)

