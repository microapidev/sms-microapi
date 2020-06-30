from rest_framework import serializers
from .models import User, Receipent, Message


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name", "phoneNumber", "email", "password")

    def save(self):
        user, created = User.objects.get_or_create(
            phoneNumber=self.validated_data['phoneNumber'], name=self.validated_data['name'], email=self.validated_data['email'])
        if created:
            user.set_password(self.validated_data['password'])
            user.save()


class RecepientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipent
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["receiver", "author", "date_created",
                  "content", "price", "status"]
