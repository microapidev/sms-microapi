from rest_framework import serializers
from .models import user, Receipent, Message


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = "__all__"


class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["receiver", "author", "date_created", "content", "price", "status"]
