from django.contrib import admin

# Register your models here.
from .models import Receipent, Group, Message

# class UserAdmin(admin.ModelAdmin):
#     list_display = ("phoneNumber", "name", "email", "is_active", "service")


admin.site.register(Receipent)
# admin.site.register(User, UserAdmin)
admin.site.register(Group)
admin.site.register(Message)

