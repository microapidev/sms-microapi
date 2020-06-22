from rest_framework import serializers
from .models import user, Receipent

class userserializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = "__all__"

class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = "__all__"
