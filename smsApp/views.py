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

=======
from django.http import JsonResponse

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view

from .models import Receipent
from .serializers import RecepientSerializer


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
