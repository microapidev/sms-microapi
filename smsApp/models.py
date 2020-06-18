from django.db import models

# Create your models here.
class user(models.Model):
    user_name       = models.CharField(max_length = 20)
    email           = models.EmailField(max_length = 100)
    phone_number    = models.CharField(unique = True, max_length = 20)

    def __str__(self):
        return self.phone_number
