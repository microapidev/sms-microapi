from django.contrib import admin

# Register your models here.
from .models import Recipient, Group, Message, GroupNumbers

# class UserAdmin(admin.ModelAdmin):
#     list_display = ("phoneNumber", "name", "email", "is_active", "service")

class MessageAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'receiver', 'date_created','language','messageStatus',)
    list_filter = ('service_type',)
    search_fields = ('receiver',)




admin.site.register(Recipient)
# admin.site.register(User, UserAdmin)
admin.site.register(Group)
admin.site.register(GroupNumbers)
admin.site.register(Message, MessageAdmin)

