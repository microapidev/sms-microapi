from rest_framework import serializers
from .models import Receipent, Message, Group


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = user
#         fields = "__all__"


class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["receiver", "transactionID", "date_created", "content", "status", "senderID"]


class GroupSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Group
        fields = "__all__"
