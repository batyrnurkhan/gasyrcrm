from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    title = models.CharField(max_length=255)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)
    
    def __str__(self):
        return self.title
    
class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.message