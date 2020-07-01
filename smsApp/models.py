from django.db import models
import uuid
from django.utils import timezone
# from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage
# from .managers import CustomUserManager

# Create your models here.
# uploads = FileSystemStorage(location='/media/uploads')

# class User(AbstractUser):
#     username = None
#     email = models.EmailField(unique=True) 
#     name = models.CharField(max_length=30)
#     phoneNumber = models.CharField(max_length=100, unique=True)
#     otp = models.CharField(max_length=6)
#     is_active = models.BooleanField(default=False)
#     service = models.CharField(max_length=50, default="twillo")

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ["name", "phoneNumber"]

#     objects = CustomUserManager()

#     def __str__(self):
#         return self.phoneNumber

class Group(models.Model):
    groupID = models.UUIDField()
    userID = models.CharField(max_length=30) #creator of the group
    groupName = models.CharField(max_length=80)
    phoneNumbers = models.CharField(max_length=100)
    dateCreated = models.DateTimeField(default=timezone.now)

class Receipent(models.Model):
    userID = models.CharField(max_length=30) #user who added the recipient
    recipientName = models.CharField(max_length=80)
    recipientNumber = models.CharField(max_length=80)
    dateCreated = models.DateTimeField(default=timezone.now)

class Message(models.Model):
    transactionID = models.UUIDField(default=uuid.uuid4, unique=True)
    receiver = models.CharField(max_length=80)
    senderID = models.CharField(max_length=30) 
    # account_sid = models.CharField(max_length=80, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    # price = models.FloatField(blank=True, null=True)
    # status = models.CharField(max_length=100, default="Sent", blank=True, null=True)
    INFOBIP = 'IF'
    TWILLO = 'TW'
    NUOBJECT = 'NU'
    MSG91 = 'MS'
    SERVICE_CHOICES = [
        (INFOBIP, 'IF'),
        (TWILLO, 'TW'),
        (NUOBJECT, 'NU'),       
		(MSG91, 'MS'),
    ]
    service_type = models.CharField(
        max_length=2,
        choices=SERVICE_CHOICES
    )
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

# class Media(models.Model):
#     senderID = models.CharField(max_length=30) 
#     messageID = models.ForeignKey(Message,on_delete=models.CASCADE)
#     media = models.ImageField(storage=uploads) ##catering for only images at the moment

#     def __str__(self):
#         return self.id