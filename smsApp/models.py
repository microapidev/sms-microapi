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
    senderID = models.CharField(max_length=30, default="user") #creator of the group123e4567-e89b-12d3-a456-426652340000
    groupID = models.UUIDField(default=uuid.uuid4, editable=False)
    dateCreated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.groupName

class GroupNumbers(models.Model):
    group = models.ForeignKey(Group, related_name="numbers", on_delete=models.CASCADE)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phoneNumbers = models.CharField(max_length=20000, blank=False) 
    dateCreated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.phoneNumbers

class Recipient(models.Model):
    userID = models.CharField(primary_key=True, max_length=30) #user who added the recipient
    recipientName = models.CharField(max_length=80)
    recipientNumber = models.CharField(max_length=80)
    dateCreated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'id {self.userID}, number {self.recipientNumber}'

class Message(models.Model):
    transactionID = models.CharField(max_length=2000, blank=True, null=True)
    messageID = models.UUIDField(default=uuid.uuid4)
    grouptoken = models.UUIDField(null=True)
    receiver = models.CharField(max_length=80)
    senderID = models.CharField(max_length=30)
    scheduled_task_id= models.CharField(null=True, max_length=30)
    date_created = models.DateTimeField(default=timezone.now)
    content = models.TextField(max_length=500)
    INFOBIP = 'IF'
    TWILLO = 'TW'
    TELESIGN = 'TS'
    MSG91 = 'MS'
    SERVICE_CHOICES = [
        (INFOBIP, 'IF'),
        (TWILLO, 'TW'),
        (TELESIGN, 'TS'),
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
    PENDING= 'P'
    UNDELIVERED = 'U'
    MESSAGE_CHOICES = [
        (DRAFT, 'D'),
        (PENDING, 'P'),
        (SENT, 'S'),
        (UNDELIVERED, 'U'),
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
    
    LANG_CHOICES = (


        ('af', 'af'),
        ('sq', 'sq'),
        ('am', 'am'),
        ('ar', 'ar'),
        ('hy', 'hy'),
        ('az', 'az'),
        ('eu', 'eu'),
        ('be', 'be'),
        ('bn', 'bn'),
        ('bs', 'bs'),
        ('bg', 'bg'),
        ('ca', 'ca'),
        ('ceb', 'ceb'),
        ('ny', 'ny'),
        ('zh-cn', 'zh-cn'),
        ('zh-tw', 'zh-tw'),
        ('co', 'co'),
        ('hr', 'hr'),
        ('cs', 'cs'),
        ('da', 'da'),
        ('nl', 'nl'),
        ('en', 'en'),
        ('eo', 'eo'),
        ('et', 'et'),
        ('tl', 'tl'),
        ('fi', 'fi'),
        ('fr', 'fr'),
        ('fy', 'fy'),
        ('gl', 'gl'),
        ('ka', 'ka'),
        ('de', 'de'),
        ('el', 'el'),
        ('gu', 'gu'),
        ('ht', 'ht'),
        ('ha', 'ha'),
        ('haw', 'haw'),
        ('iw', 'iw'),
        ('hi', 'hin'),
        ('hmn', 'hmn'),
        ('hu', 'hu'),
        ('is', 'is'),
        ('ig', 'ig'),
        ('id', 'id'),
        ('ga', 'ga'),
        ('it', 'it'),
        ('ja', 'ja'),
        ('jw', 'jw'),
        ('kn', 'kn'),
        ('kk', 'kk'),
        ('km', 'km'),
        ('ko', 'ko'),
        ('ku', 'ku'),
        ('ky', 'ky'),
        ('lo', 'la'),
        ('la', 'la'),
        ('lv', 'lv'),
        ('lt', 'lt'),
        ('lb', 'lb'),
        ('mk', 'mk'),
        ('mg', 'mg'),
        ('ms', 'ms'),
        ('ml', 'ml'),
        ('mt', 'mt'),
        ('mi', 'mi'),
        ('mr', 'mr'),
        ('mn', 'mn'),
        ('my', 'my'),
        ('ne', 'ne'),
        ('no', 'no'),
        ('ps', 'ps'),
        ('fa', 'fa'),
        ('pl', 'pl'),
        ('pt', 'pt'),
        ('pa', 'pa'),
        ('ro', 'ro'),
        ('ru', 'ru'),
        ('sm', 'sm'),
        ('gd', 'gd'),
        ('sr', 'sr'),
        ('st', 'st'),
        ('sn', 'sn'),
        ('sd', 'si'),
        ('si', 'si'),
        ('sk', 'sk'),
        ('sl', 'sl'),
        ('so', 'so'),
        ('es', 'es'),
        ('su', 'su'),
        ('sw', 'sw'),
        ('sv', 'sv'),
        ('tg', 'tg'),
        ('ta', 'ta'),
        ('te', 'te'),
        ('th', 'th'),
        ('tr', 'tr'),
        ('uk', 'uk'),
        ('ur', 'ur'),
        ('uz', 'uz'),
        ('vi', 'vi'),
        ('cy', 'cy'),
        ('xh', 'xh'),
        ('yi', 'yi'),
        ('yo', 'yo'),
        ('zu', 'zu'),
        ('fil', 'Fil'),
        ('he', 'He'),
    
    )
    language = models.CharField(max_length=5, choices=LANG_CHOICES, default='en', blank=True, null=True)

    def __str__(self):
        return f'''service-{self.service_type}, 
                    receiver-{self.receiver}, 
                    transactionID-{self.transactionID}, 
                    groutoken-{self.grouptoken}, 
                    senderID-{self.senderID},
                    scheduled_task_id-{self.scheduled_task_id},
                    date_created-{self.date_created},
                    content-{self.content},
                    messageStatus{self.messageStatus},
                    dateScheduled{self.dateScheduled}
                    
                     '''


# class Media(models.Model):
#     senderID = models.CharField(max_length=30) 
#     messageID = models.ForeignKey(Message,on_delete=models.CASCADE)
#     media = models.ImageField(storage=uploads) ##catering for only images at the moment

#     def __str__(self):
#         return self.id