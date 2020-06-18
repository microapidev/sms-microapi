from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view

from .models import Receipent
from .serializers import RecepientSerializer

# Create your views here.


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
