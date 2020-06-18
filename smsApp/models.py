from django.db import models
import uuid
# Create your models here.
class Receipent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    email = models.CharField(unique=True, max_length=50, null=True)
    phone_number = models.CharField(unique=True, null=True, blank=False, max_length=100)
