from rest_framework import serializers
from .models import Course, Module, Lesson, LessonLiterature, Homework


class LiteratureSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = LessonLiterature
        fields = ['id', 'file', 'literature_name', 'literature_type', 'lesson']

    def update(self, instance, validated_data):
        # Update fields if they are present in the request
        instance.literature_name = validated_data.get('literature_name', instance.literature_name)
        instance.literature_type = validated_data.get('literature_type', instance.literature_type)
        instance.lesson = validated_data.get('lesson', instance.lesson)

        # Only update the file if a new file is provided
        new_file = validated_data.get('file', None)
        if new_file:
            instance.file = new_file

        instance.save()
        return instance


class HomeworkSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)

    def validate_file(self, value):
        print("Validating file:", value)  # Debug statement
        if value:
            file_type = value.name.split('.')[-1].lower()
            if file_type not in ['pdf', 'doc', 'docx', 'jpg', 'png', 'txt']:
                raise serializers.ValidationError("Invalid file type. Allowed types: pdf, doc, docx, jpg, png, txt.")
        return value

    class Meta:
        model = Homework
        fields = ['id', 'file', 'homework_name', 'lesson']


class LessonFullSerializer(serializers.ModelSerializer):
    literatures = LiteratureSerializer(many=True, required=False)
    id = serializers.IntegerField(required=False)
    homeworks = HomeworkSerializer(many=True, required=False)

    class Meta:
        model = Lesson
        fields = ['id', 'lesson_name', 'video_link', 'literatures', 'homeworks']

    def create(self, validated_data):
        literatures_data = validated_data.pop('literatures', [])
        lesson = Lesson.objects.create(**validated_data)

        for literature_data in literatures_data:
            LessonLiterature.objects.create(lesson=lesson, **literature_data)

        return lesson

    def update(self, instance, validated_data):
        literatures_data = validated_data.pop('literatures', None)

        if literatures_data is not None:
            for literature_data in literatures_data:
                literature_id = literature_data.get('id')
                if literature_id:
                    literature = LessonLiterature.objects.get(id=literature_id, lesson=instance)
                    literature.file = literature_data.get('file', literature.file)
                    literature.literature_name = literature_data.get('literature_name', literature.literature_name)
                    literature.literature_type = literature_data.get('literature_type', literature.literature_type)
                    literature.save()
                else:
                    LessonLiterature.objects.create(lesson=instance, **literature_data)

        return super().update(instance, validated_data)

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
                                # Only update literature if a file is provided or other fields are non-empty
                                for key, value in literature.items():
                                    if value is not None and value != '':
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
                                    if value is not None and value != '':
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


