# models.py
import os

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

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
            raise ValidationError('Image file is required for image-based questions.')
        if self.question_type == 'AUD' and not self.audio:
            raise ValidationError('Audio file is required for audio-based questions.')

    def __str__(self):
        return self.text if self.text else f"Question ID: {self.id} - {self.get_question_type_display()}"


@receiver(models.signals.post_delete, sender=Question)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
    if instance.audio:
        if os.path.isfile(instance.audio.path):
            os.remove(instance.audio.path)


@receiver(models.signals.pre_save, sender=Question)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_image = Question.objects.get(pk=instance.pk).image
        old_audio = Question.objects.get(pk=instance.pk).audio
    except Question.DoesNotExist:
        return False
    if old_image:
        new_file = instance.image
        if not old_image == new_file:
            if os.path.isfile(old_image.path):
                os.remove(old_image.path)
    if old_audio:
        new_file = instance.audio
        if not old_audio == new_file:
            if os.path.isfile(old_audio.path):
                os.remove(old_audio.path)


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
    course_picture = models.ImageField(upload_to="course_pictures/", default='static/core/images/course-default-bg.png')
    big_description = models.TextField()
    course_time = models.PositiveIntegerField(help_text="Duration in hours")
    course_difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)
    full_description = models.TextField()
    users = models.ManyToManyField(CustomUser, related_name='courses', blank=True)
    created_by = models.ForeignKey(CustomUser, related_name='created_courses', on_delete=models.CASCADE)
    course_success_video = models.CharField(max_length=255, blank=True, null=True)
    published = models.BooleanField(default=False)
    tests = GenericRelation(Test)

    ##publish true false
    def is_user_enrolled(self, user):
        return self.users.filter(pk=user.pk).exists()

    def calculate_completion_percentage(self, user):
        """Calculate what percentage of the course the user has completed based on tests."""
        course_ct = ContentType.objects.get_for_model(Course)
        module_ct = ContentType.objects.get_for_model(Module)
        lesson_ct = ContentType.objects.get_for_model(Lesson)

        total_tests = Test.objects.filter(
            content_type__in=[course_ct, module_ct, lesson_ct],
            object_id__in=[self.pk] + list(self.modules.values_list('pk', flat=True)) + list(
                self.modules.values_list('lessons__pk', flat=True))
        ).count()

        if total_tests == 0:
            return 0

        submitted_tests_count = Test.objects.filter(
            content_type__in=[course_ct, module_ct, lesson_ct],
            object_id__in=[self.pk] + list(self.modules.values_list('pk', flat=True)) + list(
                self.modules.values_list('lessons__pk', flat=True)),
            test_submissions__user=user
        ).distinct().count()

        return (submitted_tests_count / total_tests) * 100

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new course
        super().save(*args, **kwargs)
        if is_new:
            # Automatically create a module when a new course is created
            Module.objects.create(course=self, module_name="Default Module")

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
    LITERATURE_TYPE_CHOICES = [
        ('Book', 'Book'),
        ('Video', 'Video'),
        ('Text', 'Text'),
        ('Audio', 'Audio'),
        ('Generic', 'Generic')
    ]

    lesson = models.ForeignKey(Lesson, related_name='literatures', on_delete=models.CASCADE)
    literature_name = models.CharField(max_length=255)
    literature_type = models.CharField(max_length=20, choices=LITERATURE_TYPE_CHOICES, default='Generic')
    file = models.FileField(upload_to='literature_files/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        print(f"Saving LessonLiterature with file: {self.file}")
        super().save(*args, **kwargs)
    def __str__(self):
        return self.literature_name


class TestSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_submissions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='test_submissions')
    score = models.FloatField(default=0.0)
    completed = models.DateTimeField(auto_now_add=True)
    selected_answers = models.ManyToManyField(Answer, related_name="user_checked_answers")

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

class Homework(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='homeworks', on_delete=models.CASCADE)
    homework_name = models.CharField(max_length=100)
    file = models.FileField(upload_to="homework_files/")

    def __str__(self):
        return self.homework_name