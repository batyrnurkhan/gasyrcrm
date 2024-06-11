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

class TaskSubmission(models.Model):
    task = models.ForeignKey(Task, related_name='submissions', on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='submission_files/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.task.name}"

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
    google_meet_link = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.group_name} - {self.subject.name}"

class VolunteerChannel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='volunteer_channel_images/', null=True, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, limit_choices_to={'role': 'Mentor'})
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_channels')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.image:
            image_filenames = [
                'cat1.svg', 'cat2.svg', 'cat3.svg',
                'cat4.svg', 'cat5.svg', 'cat6.svg'
            ]
            image_filename = random.choice(image_filenames)
            self.image.name = os.path.join(settings.CATS_VOLUNTEER_IMAGES, image_filename)
        super(VolunteerChannel, self).save(*args, **kwargs)

class Grade(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'Student'})
    lesson = models.ForeignKey(Lesson_crm2, on_delete=models.CASCADE)
    date_assigned = models.DateField()
    grade = models.CharField(max_length=10)
    max_grade = models.IntegerField()
    file = models.FileField(upload_to='grade_files/', null=True, blank=True)

    def __str__(self):
        return f"{self.grade} for {self.student.full_name} on {self.date_assigned}"


class Achievement(models.Model):
    name = models.CharField(max_length=255)
    difficulty = models.IntegerField()

    def __str__(self):
        return self.name

class StudentAchievement(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.achievement}"