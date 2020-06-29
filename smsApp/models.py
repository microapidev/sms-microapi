from django.db import models
from django.db.models.signals import post_save
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage
from .managers import CustomUserManager
from django.dispatch import receiver
from django.conf import settings
from rest_framework.authtoken.models import Token
# Create your models here.
uploads = FileSystemStorage(location='/media/uploads')

class User(AbstractUser):
    email = models.EmailField(unique=True) 
    name = models.CharField(max_length=30)
    phoneNumber = models.CharField(max_length=100, unique=True)
    otp = models.CharField(max_length=6)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'phoneNumber'
    REQUIRED_FIELDS = ["name", "email"]

    objects = CustomUserManager()

    def __str__(self):
        return self.phoneNumber


class Group(models.Model):
    groupID = models.UUIDField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    groupName = models.CharField(max_length=80)
    dateCreated = models.DateTimeField(default=timezone.now)


class Receipent(models.Model):
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   groupID = models.ForeignKey(Group, on_delete=models.CASCADE)


class Message(models.Model):
    receiver = models.CharField(max_length=80)
    # author = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    account_sid = models.CharField(max_length=80, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    price = models.FloatField(blank=True, null=True)
    status = models.CharField(max_length=100, default="Sent", blank=True, null=True)
    DRAFT = 'D'
    SENT = 'S'
    FAILED = 'F'
    RECEIVED = 'R'
    SCHEDULED = 'SC'
    MESSAGE_CHOICES = [
        (DRAFT, 'D'),
        (SENT, 'S'),
        (FAILED, 'F'),       
		(RECEIVED, 'R'),    
		(SCHEDULED, 'SC'),
    ]
    messageStatus = models.CharField(
        max_length=2,
        choices=MESSAGE_CHOICES,
        default=DRAFT,
    )
    dateScheduled = models.DateTimeField(null=True)

class Media(models.Model):
    author = models.ForeignKey(User,on_delete=models.CASCADE)
    messageID = models.ForeignKey(Message,on_delete=models.CASCADE)
    media = models.ImageField(storage=uploads) ##catering for only images at the moment



    def __str__(self):
        return self.id

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)