from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, User
from django.core.files.storage import FileSystemStorage

# Create your models here.
uploads = FileSystemStorage(location='/media/uploads')

class user(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    phoneNumber = models.CharField(max_length=100, unique=True)

    USERNAME_FIELD = 'phoneNumber'
    REQUIRED_FIELDS = [name, phoneNumber, email]

    def __str__(self):
        return self.phoneNumber


class Group(models.Model):
    groupID = models.UUIDField()
    sender = models.ForeignKey(user, on_delete=models.CASCADE)
    groupName = models.CharField(max_length=80)
    dateCreated = models.DateTimeField(default=timezone.now)


class Receipent(models.Model):
   user = models.OneToOneField(user, on_delete=models.CASCADE)
   groupID = models.ForeignKey(Group, on_delete=models.CASCADE)


class Message(models.Model):
    receiver = models.CharField(max_length=80)
    # author = models.ForeignKey(user, on_delete=models.CASCADE, default=1)
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
    author = models.ForeignKey(user,on_delete=models.CASCADE)
    messageID = models.ForeignKey(Message,on_delete=models.CASCADE)
    media = models.ImageField(storage=uploads) ##catering for only images at the moment



    def __str__(self):
        return self.id

