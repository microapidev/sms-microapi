from django.db import models
import uuid
from django.utils import timezone
# from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
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


class Group(models.Model):
    # groupID = models.ForeignKey(GroupUnique, related_name='grp_id', on_delete=models.SET_NULL)
    groupName = models.CharField(max_length=90)
    userID = models.CharField(max_length=30, default="user") #creator of the group123e4567-e89b-12d3-a456-426652340000
    groupID = models.UUIDField(default=uuid.uuid4, editable=False)
    dateCreated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.groupName

class GroupNumbers(models.Model):
    group = models.ForeignKey(Group, related_name='group', on_delete=models.CASCADE)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phoneNumbers = models.CharField(validators=[phone_regex], max_length=200, blank=True) # validators should be a list
    dateCreated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.phoneNumbers

class Receipent(models.Model):
    userID = models.CharField(primary_key=True, max_length=30) #user who added the recipient
    recipientName = models.CharField(max_length=80)
    recipientNumber = models.CharField(max_length=80)
    dateCreated = models.DateTimeField(default=timezone.now)

class Message(models.Model):
    transactionID = models.UUIDField(default=uuid.uuid4)
    receiver = models.CharField(max_length=80)
    senderID = models.CharField(max_length=30) 
    # account_sid = models.CharField(max_length=80, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    content = models.TextField(default="test")
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