from django.db import models
from django.conf import settings
import os
import random
from django.core.files import File
from chats.models import ChatRoom
from schedule.models import Shift, ShiftTime
from users.models import CustomUser
from django.apps import apps

class Task(models.Model):
    chat_room = models.ForeignKey('chats.ChatRoom', related_name='tasks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    deadline = models.DateTimeField()
    file = models.FileField(upload_to='task_files/', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')

    def __str__(self):
        return self.name

# Create your models here.
class Subject(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='subject_images/', blank=True, null=True)  # Add this line

    def __str__(self):
        return self.name


class GroupTemplate(models.Model):
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(CustomUser, limit_choices_to={'role': 'Student'})
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

class Lesson_crm2(models.Model):
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'Mentor'})
    teacher = models.ForeignKey(CustomUser, related_name='assigned_lessons', on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'Teacher'})
    group_name = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group_template = models.ForeignKey(GroupTemplate, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='lessons')
    time_slot = models.ForeignKey(ShiftTime, related_name='lessons', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.group_name} - {self.subject.name}"

class VolunteerChannel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='volunteer_channel_images/', null=True, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'Mentor'})
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.image:
            image_filenames = [
                'кот 1.svg', 'кот 1-1.svg', 'кот 1-2.svg',
                'кот 1-3.svg', 'кот 1-4.svg', 'кот 1-5.svg'
            ]
            image_path = os.path.join(settings.CATS_VOLUNTEER_IMAGES, random.choice(image_filenames))
            with open(image_path, 'rb') as f:
                self.image.save(os.path.basename(image_path), File(f), save=False)
        super(VolunteerChannel, self).save(*args, **kwargs)

class Grade(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'Student'})
    lesson = models.ForeignKey(Lesson_crm2, on_delete=models.CASCADE)
    date_assigned = models.DateField()
    grade = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.grade} for {self.student.full_name} on {self.date_assigned}"