from rest_framework import serializers
from .models import CustomUser, Subject, GroupTemplate, Lesson_crm2, Task, TaskSubmission


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'phone_number', 'role']

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class GroupTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupTemplate
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    teacher = CustomUserSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='Teacher'),
        source='teacher',
        write_only=True
    )
    google_meet_link = serializers.URLField(allow_blank=True, required=False)

    class Meta:
        model = Lesson_crm2
        fields = ['id', 'mentor', 'teacher', 'teacher_id', 'group_name', 'subject', 'group_template', 'google_meet_link']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'deadline', 'file', 'chat_room']


class FileUploadSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    file = serializers.FileField()

class TaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = ['task', 'student', 'file']