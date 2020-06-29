from rest_framework import serializers
from .models import User, Receipent, Message


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "phoneNumber", "email")


class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["receiver", "author", "date_created", "content", "price", "status"]
