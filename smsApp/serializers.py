from rest_framework import serializers
from .models import Recipient, Message, Group, GroupNumbers, SenderDetails, Sender
import uuid



# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = user
#         fields =  "__all__"


class RecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipient
        fields = ["recipientName", "recipientNumber", "senderID"]


class MessageSerializer(serializers.ModelSerializer):
    SERVICE_CHOICES = [
        ('INFOBIP', 'IF'),
        ('TWILLO', 'TW'),
        ('TELESIGN', 'TS'),       
		('MSG91', 'MS'),
    ]
    service_type = serializers.ChoiceField(choices=Message.SERVICE_CHOICES)
    grouptoken = serializers.CharField(read_only=True)
    # dateScheduled = serializers.DateField(input_formats="%Y-%m-%dT%H:%M:%S.%fZ")
    date_created = serializers.CharField(read_only=True)
    messageStatus = serializers.ChoiceField(choices=['D', 'S','F','R','P','U','SC'], read_only=True)
    language = serializers.ChoiceField(choices=Message.LANG_CHOICES, default='en', required=False)
    transactionID = serializers.CharField(read_only=True)
    messageID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)

    class Meta:
        model = Message
        fields = ["senderID", "content", "receiver", "service_type", "messageStatus", "date_created", "transactionID", "grouptoken", "language", "messageID", "dateScheduled"]


class GroupSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)
    groupName = serializers.CharField(required=True)
    groupID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)
    numbers = serializers.StringRelatedField(many=True, read_only=True)
    class Meta:
        model = Group
        fields = ["groupName", "groupID", "dateCreated", "numbers"]
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

class SenderSerializer(serializers.ModelSerializer):
    sender_details = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = Sender
        fields = ("senderID", "sender_details")


class SenderDetailsSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="senderID.senderID", required=True)
    sid = serializers.CharField(max_length=1200, required=True)
    token = serializers.CharField(max_length=1200, required=True)
    SERVICE_CHOICES = [
        ("INFOBIP", 'IF'),
        ("TWILLO", 'TW'),
        ("TELESIGN", 'TS'),       
		("MSG91", 'MS'),
    ]
    service_name = serializers.ChoiceField(choices=SERVICE_CHOICES, required=True)

    def create(self, validated_data):
        senderID = validated_data["senderID"]["senderID"]
        senderID = Sender.objects.get(senderID=senderID)
        validated_data["senderID"] = senderID
        return SenderDetails.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.token = validated_data.get('token', instance.token)
        instance.sid = validated_data.get('sid', instance.sid)
        instance.save()
        return instance


    class Meta:
        model = SenderDetails
        fields = ("sid", "token", "service_name", "sender")

    