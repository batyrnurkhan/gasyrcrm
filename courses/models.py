# models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()

class Test(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

class Question(models.Model):
    TYPE_CHOICES = [
        ('SC', 'Single Choice'),
        ('MC', 'Multiple Choice'),
        ('IMG', 'Image Based'),
        ('AUD', 'Audio Based')
    ]

    test = models.ForeignKey('Test', related_name='questions', on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)  # Allow blank for non-text questions
    question_type = models.CharField(max_length=3, choices=TYPE_CHOICES, default='SC')
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)
    audio = models.FileField(upload_to='question_audio/', blank=True, null=True)

    def clean(self):
        # Validate based on question_type
        if self.question_type == 'IMG' and not self.image:
            raise ValidationError(_('Image file is required for image-based questions.'))
        if self.question_type == 'AUD' and not self.audio:
            raise ValidationError(_('Audio file is required for audio-based questions.'))

    def __str__(self):
        return self.text if self.text else f"Question ID: {self.id} - {self.get_question_type_display()}"

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
    ##publish true false
    def is_user_enrolled(self, user):
        return self.users.filter(pk=user.pk).exists()

    def calculate_completion_percentage(self, user):
        """Calculate what percentage of the course the user has completed based on tests."""
        total_tests = Test.objects.filter(
            content_type=ContentType.objects.get_for_model(Course),
            object_id=self.pk
        ).count()

        if total_tests == 0:
            return 0  # Avoid division by zero

        submitted_tests_count = Test.objects.filter(
            content_type=ContentType.objects.get_for_model(Course),
            object_id=self.pk,
            test_submissions__user=user  # Assumes existence of a TestSubmission model relating users to tests
        ).distinct().count()

        return (submitted_tests_count / total_tests) * 100

    def __str__(self):
        return self.course_name


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    module_name = models.CharField(max_length=50)
    tests = GenericRelation(Test)

    def __str__(self):
        return self.module_name

class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    lesson_name = models.CharField(max_length=24)
    video_link = models.CharField(max_length=200)
    tests = GenericRelation(Test)  # This allows the reverse relation using 'tests'

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

from django.conf import settings

class TestSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_submissions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='test_submissions')
    score = models.FloatField(default=0.0)
    completed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.test.title} - Score: {self.score}"


class Rating(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_ratings')
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_ratings')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # Assuming a rating scale of 1-5

    class Meta:
        unique_together = ['course', 'student', 'teacher']  # Prevent duplicate ratings

    def __str__(self):
        return f"{self.rating}/5 by {self.teacher.full_name} for {self.student.full_name} in {self.course.course_name}"