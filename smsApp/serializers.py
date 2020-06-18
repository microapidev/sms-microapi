from rest_framework import serializers

from .models import Receipent


class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = '__all__'
