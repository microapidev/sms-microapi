from django.db import models
import uuid
# Create your models here.
class user(models.Model):
    user_name       = models.CharField(max_length = 20)
    email           = models.EmailField(max_length = 100)
    phone_number    = models.CharField(unique = True, max_length = 20)

    def __str__(self):
        return self.phone_number
=======
class Receipent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=False)
    email = models.CharField(unique=True, max_length=50, null=True)
    phone_number = models.CharField(unique=True, null=True, blank=False, max_length=100)

