from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage
from .managers import CustomUserManager
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

# Create your models here.
uploads = FileSystemStorage(location='/media/uploads')

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True) 
    name = models.CharField(max_length=30)
    phoneNumber = models.CharField(max_length=100, unique=True)
    otp = models.CharField(max_length=6)
    is_active = models.BooleanField(default=False)
    service = models.CharField(max_length=50, default="twillo")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["name", "phoneNumber"]

    objects = CustomUserManager()

    def __str__(self):
        return self.phoneNumber

# class GroupUnique(models.Model):
#     groupName = models.CharField(max_length=80, default='grp1')
#     user = models.ForeignKey(User, verbose_name='owner', on_delete=models.CASCADE)
#     dateCreated = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return self.groupName

class Group(models.Model):
    # groupID = models.ForeignKey(GroupUnique, related_name='grp_id', on_delete=models.SET_NULL)
    groupName = models.CharField(max_length=80, default='grp1')
    user = models.ForeignKey(User, default=2, verbose_name='owner', on_delete=models.CASCADE)
    groupID = models.UUIDField(default=uuid.uuid4)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    recipient = models.CharField(validators=[phone_regex], max_length=15, blank=True) # validators should be a list
    dateCreated = models.DateTimeField(default=timezone.now)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(str(value))

    def __str__(self):
        return self.groupName




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

