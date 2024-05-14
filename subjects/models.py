from django.db import models

from users.models import CustomUser


# Create your models here.
class Subject(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

class GroupTemplate(models.Model):
    name = models.CharField(max_length=255)
    students = models.ManyToManyField(CustomUser, limit_choices_to={'role': 'Student'})

    def __str__(self):
        return self.name

class Lesson_crm2(models.Model):
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'Mentor'})
    teacher = models.ForeignKey(CustomUser, related_name='assigned_lessons', on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'Teacher'})
    group_name = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group_template = models.ForeignKey(GroupTemplate, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.group_name} - {self.subject.name}"
