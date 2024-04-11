from django.db import models
from users.models import CustomUser


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

    def __str__(self):
        return self.course_name


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    module_name = models.CharField(max_length=50)
    module_test = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.module_name


class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    lesson_name = models.CharField(max_length=24)
    video_link = models.CharField(max_length=200)
    lesson_test = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.lesson_name


class LessonLiterature(models.Model):
    LITERATURE_TYPES = (
        ('Book', 'Book'),
        ('Video', 'Video'),
        ('Text', 'Text'),
        ('Audio', 'Audio'),
    )

    lesson = models.ForeignKey(Lesson, related_name='literatures', on_delete=models.CASCADE)
    literature_name = models.CharField(max_length=20)
    literature_type = models.CharField(max_length=6, choices=LITERATURE_TYPES)
    file = models.FileField(upload_to="lesson_literature")

    def __str__(self):
        return self.literature_name
