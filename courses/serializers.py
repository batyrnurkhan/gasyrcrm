from rest_framework import serializers
from .models import Course, Module, Lesson, LessonLiterature, Homework


class LiteratureSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)

    def validate_file(self, value):
        # If the value is a string, assume it's a file path and skip validation
        if isinstance(value, str):
            return value

        if value is None:
            raise serializers.ValidationError("This field cannot be empty.")

        # Assuming the uploaded file is passed, check its type
        file_type = value.name.split('.')[-1].lower()
        if file_type not in ['pdf', 'doc', 'docx', 'jpg', 'png', 'txt']:
            raise serializers.ValidationError("Invalid file type.")

        return value

    class Meta:
        model = LessonLiterature
        fields = ['id', 'file', 'literature_name', 'literature_type', 'lesson']


class HomeworkSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)

    def validate_file(self, value):
        # Allow any file type, so no validation on file extensions
        if value is None or value == '':
            raise serializers.ValidationError("This field cannot be empty.")
        return value

    class Meta:
        model = Homework
        fields = ['id', 'file', 'homework_name', 'lesson']


class LessonFullSerializer(serializers.ModelSerializer):
    literatures = LiteratureSerializer(many=True)
    id = serializers.IntegerField(required=False)
    homeworks = HomeworkSerializer(many=True)


    def save(self, **kwargs):
        # Directly manipulate self.validated_data if needed
        if 'lesson_name' in self.validated_data:
            lesson_name = self.validated_data['lesson_name']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['lesson_name'] = lesson_name.encode('utf-8', 'ignore').decode('utf-8')
        if 'video_link' in self.validated_data:
            video_link = self.validated_data['video_link']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['video_link'] = video_link.encode('utf-8', 'ignore').decode('utf-8')

        # Call the superclass method to actually save the data
        return super(LessonFullSerializer, self).save(**kwargs)

    class Meta:
        model = Lesson
        fields = ['id', 'lesson_name', 'video_link', 'literatures', 'homeworks']
    
    def create(self, validated_data):
        validated_data.pop("literatures")
        return super().create(validated_data)


class LessonSerializer(serializers.ModelSerializer):
    def save(self, **kwargs):
        # Directly manipulate self.validated_data if needed
        if 'lesson_name' in self.validated_data:
            lesson_name = self.validated_data['lesson_name']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['lesson_name'] = lesson_name.encode('utf-8', 'ignore').decode('utf-8')
        if 'video_link' in self.validated_data:
            video_link = self.validated_data['video_link']
            # Example operation, though this might be redundant if encoding is handled:
            self.validated_data['video_link'] = video_link.encode('utf-8', 'ignore').decode('utf-8')

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
            self.validated_data['module_name'] = module_name.encode('utf-8', 'ignore').decode('utf-8')

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
                    setattr(module, key, value)
                module.save()

                for lesson_data in lessons_data:
                    lesson_id = lesson_data.get('id', None)
                    literature_data = lesson_data.pop('literatures', [])
                    homeworks_data = lesson_data.pop('homeworks', [])

                    if lesson_id:
                        lesson = Lesson.objects.get(id=lesson_id, module=module)
                        for key, value in lesson_data.items():
                            setattr(lesson, key, value)
                        lesson.save()

                        # Handle literatures
                        literatures = []
                        for literature in literature_data:
                            literature_id = literature.get('id')
                            literature_instance, created = LessonLiterature.objects.get_or_create(
                                id=literature_id,
                                defaults=literature
                            )
                            if not created:
                                print(f"Updating literature with file: {literature_instance.file}")  # Log for debugging
                                # If literature is already present, update it
                                for key, value in literature.items():
                                    setattr(literature_instance, key, value)
                                literature_instance.save()
                            literatures.append(literature_instance)
                        lesson.literatures.set(literatures)

                        # Handle homeworks (similar approach)
                        homeworks = []
                        for homework in homeworks_data:
                            homework_instance, created = Homework.objects.get_or_create(
                                id=homework.get('id'),
                                defaults=homework
                            )
                            if not created:
                                for key, value in homework.items():
                                    setattr(homework_instance, key, value)
                                homework_instance.save()
                            homeworks.append(homework_instance)
                        lesson.homeworks.set(homeworks)
                    else:
                        lesson = Lesson.objects.create(module=module, **lesson_data)

                        literatures = [LessonLiterature.objects.create(**lit) for lit in literature_data]
                        lesson.literatures.set(literatures)

                        homeworks = [Homework.objects.create(**hw) for hw in homeworks_data]
                        lesson.homeworks.set(homeworks)
            else:
                Module.objects.create(course=instance, **module_data)

        return instance


