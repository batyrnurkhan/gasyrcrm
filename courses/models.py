# models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser

class Test(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class Question(models.Model):
    test = models.ForeignKey(Test, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    QUESTION_TYPES = [
        ('SC', 'Single Choice'),
        ('MC', 'Multiple Choice'),
    ]
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES, default='SC')

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class Course(models.Model):
    DIFFICULTY_CHOICES = [
        (1, 'Very Easy'),
        (2, 'Easy'),
        (3, 'Medium'),
        (4, 'Hard'),
        (5, 'Very Hard'),
    ]
    course_name = models.CharField(max_length=100)
    mini_description = models.CharField(max_length=255)
    course_picture = models.ImageField(upload_to="course_pictures/")
    big_description = models.TextField()
    course_time = models.PositiveIntegerField(help_text="Duration in hours")
    course_difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)
    full_description = models.TextField()
    users = models.ManyToManyField(CustomUser, related_name='courses', blank=True)
    created_by = models.ForeignKey(CustomUser, related_name='created_courses', on_delete=models.CASCADE)

    def is_user_enrolled(self, user):
        """Check if a given user is enrolled in this course."""
        return self.users.filter(pk=user.pk).exists()

    def __str__(self):
        return self.course_name


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    module_name = models.CharField(max_length=50)

    def __str__(self):
        return self.module_name

class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    lesson_name = models.CharField(max_length=24)
    video_link = models.CharField(max_length=200)

    def __str__(self):
        return self.lesson_name

class LessonLiterature(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='literatures', on_delete=models.CASCADE)
    literature_name = models.CharField(max_length=20)
    literature_type = models.CharField(max_length=6, choices=[
        ('Book', 'Book'),
        ('Video', 'Video'),
        ('Text', 'Text'),
        ('Audio', 'Audio'),
    ])
    file = models.FileField(upload_to="lesson_literature")

    def __str__(self):
        return self.literature_name


