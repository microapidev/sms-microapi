from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view

from .models import Receipent
from .serializers import RecepientSerializer

from twilio.rest import Client
from django.http import HttpResponse

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

#send message using twilio
def sendmessage(request):
    number = ""
    #add twilio sid, auth token and twilio number
    account_sid = ""
    auth_token = ""
    twilio_number = ""
    
    for e in Receipent.objects.all():
        for key,value in e:
            if key == "phone_number":
                number = value     
    message = ('Hello world message')    
    clients = Client(account_sid,auth_token)
    clients.messages.create(to=number,
                            from_= twilio_number,
                            body=message)
    return HttpResponse("messages sent!", 200)