from django.db import models
import uuid
from django.utils import timezone
# from django.contrib.auth.models import AbstractUser
from django.core.files.storage import FileSystemStorage
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
# from .tasks import singleMessageSchedule
from phonenumber_field.modelfields import PhoneNumberField
# from .managers import CustomUserManager

class Sender(models.Model):
    senderID = models.CharField(max_length=65)  

    def __str__(self):
        return self.senderID


class Group(models.Model):
    # groupID = models.ForeignKey(GroupUnique, related_name='grp_id', on_delete=models.SET_NULL)
    groupName = models.CharField(max_length=90)
    senderID = models.ForeignKey(Sender,related_name='group', on_delete=models.CASCADE) #creator of the group123e4567-e89b-12d3-a456-426652340000
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
    senderID = models.ForeignKey(Sender, related_name='recipients', on_delete=models.CASCADE) #user who added the recipient
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
    senderID = models.ForeignKey(Sender, related_name='messages', on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)
    content = models.TextField(max_length=500)
    dateScheduled = models.DateField(null=True)
    scheduleID = models.UUIDField(null=True)
    INFOBIP = 'IF'
    TWILIO = 'TW'
    TELESIGN = 'TS'
    MSG91 = 'MS'
    MESSAGEBIRD = 'MB'
    GATEWAYAPI = 'GA'
    D7 = 'D7'
    SERVICE_CHOICES = [
        (INFOBIP, 'IF'),
        (TWILIO, 'TW'),
        (TELESIGN, 'TS'),       
		(MESSAGEBIRD, 'MB'),
		(GATEWAYAPI, 'GA'),

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
    EXPIRED = 'E'
    REJECTED = 'FR'

    MESSAGE_CHOICES = [
        (DRAFT, 'D'),
        (PENDING, 'P'),
        (SENT, 'S'),
        (UNDELIVERED, 'U'),
        (FAILED, 'F'),       
        (EXPIRED, 'E'),       
        (REJECTED, 'FR'),       
		(RECEIVED, 'R'),    
		(SCHEDULED, 'SC'),
    ]
    messageStatus = models.CharField(
        max_length=2,
        choices=MESSAGE_CHOICES,
        default=DRAFT,
    )
    
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
        return f'service {self.service_type}, receiver {self.receiver}'

    # def oneTimeSchedule(self):
    #     date = self.dateScheduled
    #     # task_name=f'{self.project_name}-{self.id}'        #for Periodic tasks
    #     mylist = ['list of all the args we need to send d async', content, senderID, receiver, tasknameOrid,]
    #     task = singleMessageSchedule.apply_async(args=[mylst], eta=date)
    #     self.scheduleID = task.id
    #     return self.messageID, self.scheduleID





# class Media(models.Model):
#     senderID = models.CharField(max_length=30) 
#     messageID = models.ForeignKey(Message,on_delete=models.CASCADE)
#     media = models.ImageField(storage=uploads) ##catering for only images at the moment

#     def __str__(self):
#         return self.id


class SenderDetails(models.Model):
    senderID = models.ForeignKey(Sender, related_name='details', on_delete=models.CASCADE)
    default = models.BooleanField(default=False)
    sid = models.CharField(max_length=1200)
    token = models.CharField(max_length=1300)
    verified_no = models.CharField(max_length=20000, blank=False)
    SERVICE_CHOICES = [
        ("INFOBIP", 'IF'),
        ("TWILIO", 'TW'),
        ("TELESIGN", 'TS'),       
        ("MESSAGEBIRD", 'MB'),
		("GATEWAYAPI", 'GA'),
    ]
    service_name = models.CharField(max_length=50, choices=SERVICE_CHOICES)

    def __str__(self):
        return self.service_name