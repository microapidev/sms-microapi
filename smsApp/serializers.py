from rest_framework import serializers
from .models import user

class userserializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = "__all__"
=======

from .models import Receipent


class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = '__all__'
