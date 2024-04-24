from rest_framework import serializers
from .models import Course, Module, Lesson, LessonLiterature


class LiteratureSerializer(serializers.ModelSerializer):
    literature_type = serializers.CharField(read_only=True)

    class Meta:
        model = LessonLiterature
        fields = ['id', 'file', 'literature_name', 'literature_type']


class LessonFullSerializer(serializers.ModelSerializer):
    literatures = LiteratureSerializer(many=True)

    class Meta:
        model = Lesson
        fields = ['id', 'lesson_name', 'video_link', 'literatures']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'lesson_name', 'video_link', 'module']


class ModuleFullSerializer(serializers.ModelSerializer):
    lessons = LessonFullSerializer(many=True)

    class Meta:
        model = Module
        fields = ['id', 'module_name', 'lessons']


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'module_name', 'course']


class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleFullSerializer(many=True)

    class Meta:
        model = Course
        fields = ['id', 'modules']
