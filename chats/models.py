from django.db import models
from django.conf import settings
from django.apps import apps

class ChatRoom(models.Model):
    title = models.CharField(max_length=255)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def __str__(self):
        return self.title

class Message(models.Model):
    MESSAGE_TYPES = [
        ('message', 'Message'),
        ('conf', 'Conference'),
        ('task', 'Task')
    ]

    chat_room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='message')
    timestamp = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey('subjects.Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.message_type.upper()}: {self.message if self.message else 'File Message'}"
