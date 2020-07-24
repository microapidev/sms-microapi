from  django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from .models import Recipient, Message, Group, GroupNumbers, SenderDetails, Sender
import uuid
from django.utils import timezone



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
        ('TWILIO', 'TW'),
		("MESSAGEBIRD", 'MB'),
		("GATEWAYAPI", 'GA'),
    ]
    service_type = serializers.ChoiceField(choices=Message.SERVICE_CHOICES, read_only=True)
    grouptoken = serializers.CharField(read_only=True)
    dateScheduled = serializers.DateTimeField(default=timezone.now())
    date_created = serializers.CharField(read_only=True)
    # dateScheduled = serializers.DateField()
    messageStatus = serializers.ChoiceField(choices=['D', 'S','F','R','P','U','SC'], read_only=True)
    language = serializers.ChoiceField(choices=Message.LANG_CHOICES, default='en', required=False)
    transactionID = serializers.CharField(read_only=True)
    messageID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)
    senderID = serializers.SlugRelatedField(slug_field='senderID', queryset=Sender.objects.all())

    class Meta:
        model = Message
        fields = ["senderID", "content", "receiver", "service_type", "messageStatus","dateScheduled", "date_created", "transactionID", "grouptoken", "language", "messageID"]


class GroupSerializer(serializers.ModelSerializer):
    dateCreated = serializers.DateTimeField(read_only=True)
    groupName = serializers.CharField(required=True)
    groupID = serializers.UUIDField(format='hex_verbose', initial=uuid.uuid4, read_only=True)
    numbers = serializers.StringRelatedField(many=True, read_only=True)
    senderID = serializers.SlugRelatedField(slug_field='senderID', queryset=Sender.objects.all())
    class Meta:
        model = Group
        fields = "__all__"
        depth = 1
        # fields = ["groupName", "groupID", "dateCreated", "numbers", "senderID"]

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
    token = serializers.CharField(max_length=1200, required=True, label="Token or Access key or Username")
    sid = serializers.CharField(max_length=1200, required=False, label="SID or Password")
    SERVICE_CHOICES = [
        ("INFOBIP", 'IF'),
        ("TWILIO", 'TW'),
        ("TELESIGN", 'TS'),       
		("MESSAGEBIRD", 'MB'),
		("GATEWAYAPI", 'GA'),
    ]
    service_name = serializers.ChoiceField(choices=SERVICE_CHOICES, required=True)
    verified_no = serializers.CharField(max_length=1200, required=False, label="Registered Number if any")
    default = serializers.BooleanField()

    def create(self, validated_data):
        senderID = validated_data["senderID"]["senderID"]
        senderID = Sender.objects.get(senderID=senderID)
        validated_data["senderID"] = senderID
        return SenderDetails.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.token = validated_data.get('token', instance.token)
        instance.sid = validated_data.get('sid', instance.sid)
        instance.default = validated_data.get('default', instance.default)
        instance.verified_no = validated_data.get('verified_no', instance.verified_no)
        print(instance.senderID)
        if instance.default == True:
            other_inst = SenderDetails.objects.get(senderID=instance.senderID, default=True)
            print(other_inst)
            other_inst.default = False
            other_inst.save()
        else:
            try:
                other_inst = SenderDetails.objects.get(senderID=instance.senderID, default=True)
            except ObjectDoesNotExist:
                other_inst = SenderDetails.objects.filter(senderID=instance.senderID, default=False)[0]
                other_inst.default = True
                other_inst.save()        
        instance.save()
        return instance


    class Meta:
        model = SenderDetails
        fields = ( "sender", "service_name", "token", "sid" , "verified_no", "default")

    