from rest_framework import serializers
from .models import Recipient, Message, Group, GroupNumbers
import uuid



# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = user
#         fields =  "__all__"


class RecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipient
        fields = ["recipientName", "recipientNumber", "userID"]


class MessageSerializer(serializers.ModelSerializer):
    SERVICE_CHOICES = [
        ('INFOBIP', 'IF'),
        ('TWILLO', 'TW'),
        ('TELESIGN', 'TS'),       
		('MSG91', 'MS'),
    ]
    service_type = serializers.ChoiceField(choices=Message.SERVICE_CHOICES)
    grouptoken = serializers.CharField(read_only=True)
    date_created = serializers.CharField(read_only=True)
    messageStatus = serializers.ChoiceField(choices=['D', 'S','F','R','P','U','SC'], read_only=True)
    language = serializers.ChoiceField(choices=Message.LANG_CHOICES, default='en', required=False)
    transactionID = serializers.CharField(read_only=True)
    messageID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)

    class Meta:
        model = Message
        fields = ["senderID", "content", "receiver", "service_type", "messageStatus", "date_created", "transactionID", "grouptoken", "language", "messageID"]


class GroupSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)
    groupName = serializers.CharField(required=True)
    groupID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)
    senderID = serializers.CharField(required=True)
    numbers = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Group
        fields = ["groupName", "senderID", "groupID", "dateCreated", "numbers"]
        depth = 1

class GroupNumbersSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)
    group = serializers.SlugRelatedField(slug_field='groupName', queryset=Group.objects.all())
    phoneNumbers = serializers.CharField(required=True)
    class Meta:
        model = GroupNumbers
        fields = "__all__"


class GroupNumbersPrimarySerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), required=True)
    phoneNumbers = serializers.CharField(required=True)
    class Meta:
        model = GroupNumbers
        fields = "__all__"


