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
    service_type = serializers.CharField(read_only=True)
    class Meta:
        model = Message
        fields = ["senderID", "content", "receiver", 'service_type']


class GroupSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Group
        fields = "__all__"
