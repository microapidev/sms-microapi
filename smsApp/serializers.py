from rest_framework import serializers
from .models import Receipent, Message, Group, GroupNumbers
import uuid



# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = user
#         fields =  "__all__"


class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    service_type = serializers.CharField(read_only=True)
    messageStatus = serializers.ChoiceField(choices=['D', 'S','F','R','SC'], read_only=True)
    transactionID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)
    class Meta:
        model = Message
        fields = ["senderID", "content", "receiver", "service_type", "messageStatus", "transactionID"]


class GroupSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)
    groupName = serializers.CharField(required=True)
    groupID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)
    userID = serializers.CharField(required=True)
    class Meta:
        model = Group
        fields = "__all__"

class GroupNumbersSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    phoneNumbers = serializers.CharField(required=True)
    class Meta:
        model = GroupNumbers
        fields = "__all__"
