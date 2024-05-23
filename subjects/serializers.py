from rest_framework import serializers
from .models import CustomUser, Subject, GroupTemplate, Lesson_crm2, Task, VolunteerChannel


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'phone_number', 'role']

class VolunteerChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerChannel
        fields = ['id', 'name', 'users']
        depth = 1

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

    class Meta:
        model = Lesson_crm2
        fields = ['id', 'mentor', 'teacher', 'teacher_id', 'group_name', 'subject', 'group_template']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'deadline', 'file', 'chat_room']