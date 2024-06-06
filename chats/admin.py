from django.contrib import admin

from chats.models import ChatRoom, Message

# Register your models here.
admin.site.register(Message)

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']
