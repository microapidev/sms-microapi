from django.contrib import admin

# Register your models here.
from .models import Receipent, User

class UserAdmin(admin.ModelAdmin):
    list_display = ("phoneNumber", "username", "email", "otp")


admin.site.register(Receipent)
admin.site.register(User, UserAdmin)