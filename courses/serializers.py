from rest_framework import serializers
from .models import Course, Module, Lesson, LessonLiterature


class LiteratureSerializer(serializers.ModelSerializer):
    file = serializers.CharField(read_only=True)

    def save(self, **kwargs):
        # Directly manipulate self.validated_data if needed
        if 'literature_name' in self.validated_data:
            literature_name = self.validated_data['literature_name']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['literature_name'] = literature_name.encode('utf-8').decode('utf-8')

        # Call the superclass method to actually save the data
        return super(LiteratureSerializer, self).save(**kwargs)

    class Meta:
        model = LessonLiterature
        fields = ['id', 'file', 'literature_name', 'literature_type', 'lesson']


class LessonFullSerializer(serializers.ModelSerializer):
    literatures = LiteratureSerializer(many=True)
    id = serializers.IntegerField(required=False)

    def save(self, **kwargs):
        # Directly manipulate self.validated_data if needed
        if 'lesson_name' in self.validated_data:
            lesson_name = self.validated_data['lesson_name']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['lesson_name'] = lesson_name.encode('utf-8').decode('utf-8')
        if 'video_link' in self.validated_data:
            video_link = self.validated_data['video_link']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['video_link'] = video_link.encode('utf-8').decode('utf-8')

        # Call the superclass method to actually save the data
        return super(LessonFullSerializer, self).save(**kwargs)

    class Meta:
        model = Lesson
        fields = ['id', 'lesson_name', 'video_link', 'literatures']
    
    def create(self, validated_data):
        validated_data.pop("literatures")
        return super().create(validated_data)


class LessonSerializer(serializers.ModelSerializer):
    def save(self, **kwargs):
        # Directly manipulate self.validated_data if needed
        if 'lesson_name' in self.validated_data:
            lesson_name = self.validated_data['lesson_name']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['lesson_name'] = lesson_name.encode('utf-8').decode('utf-8')
        if 'video_link' in self.validated_data:
            video_link = self.validated_data['video_link']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['video_link'] = video_link.encode('utf-8').decode('utf-8')

        # Call the superclass method to actually save the data
        return super(LessonSerializer, self).save(**kwargs)

    class Meta:
        model = Lesson
        fields = ['id', 'lesson_name', 'video_link', 'module']


class ModuleFullSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    lessons = LessonFullSerializer(many=True)

    def save(self, **kwargs):
        # Directly manipulate self.validated_data if needed
        if 'module_name' in self.validated_data:
            module_name = self.validated_data['module_name']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['module_name'] = module_name.encode('utf-8').decode('utf-8')

        # Call the superclass method to actually save the data
        return super(ModuleFullSerializer, self).save(**kwargs)

    class Meta:
        model = Module
        fields = ['id', 'module_name', 'lessons']

    def create(self, validated_data):
        validated_data.pop("lessons")
        return super().create(validated_data)


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'module_name', 'course']


class CourseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    modules = ModuleFullSerializer(many=True)

    class Meta:
        model = Course
        fields = ['id', 'modules']

    def update(self, instance, validated_data):
        modules_data = validated_data.pop('modules', [])

        for module_data in modules_data:
            module_id = module_data.get('id', None)
            if module_id:
                module = Module.objects.get(id=module_id, course=instance)
                lessons_data = module_data.pop('lessons', [])
                for key, value in module_data.items():
                    print(key, value)
                    setattr(module, key, value)
                module.save()
                for lesson_data in lessons_data:
                    lesson_id = lesson_data.get('id', None)
                    if lesson_id:
                        lesson = Lesson.objects.get(id=lesson_id, module=module)
                        literature_data = lesson_data.pop('literatures', [])
                        for key, value in lesson_data.items():
                            print(key, value)
                            setattr(lesson, key, value)
                        lesson.save()
                    else:
                        Lesson.objects.create(module=module, **lesson_data)
            else:
                Module.objects.create(course=instance, **module_data)

        return instance
