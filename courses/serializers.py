from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import mimetypes

from .models import Course, Module, Lesson, LessonLiterature, Homework
import magic


class LiteratureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonLiterature
        fields = ['id', 'lesson', 'literature_name', 'literature_type', 'file', 'created_at']

    def validate_file(self, value):
        file = value
        content_type, encoding = mimetypes.guess_type(file.name)

        print(f"Validating file with name: {file.name}, size: {file.size}, detected content_type: {content_type}")

        if content_type == 'application/pdf':
            return value
        elif content_type in ['image/jpeg', 'image/png']:
            return value
        elif content_type in ['text/plain', 'application/msword',
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return value
        elif content_type in ['audio/mpeg', 'audio/mp3']:
            return value
        else:
            raise serializers.ValidationError("Unsupported file type.")

    def create(self, validated_data):
        file = validated_data.get('file')
        content_type = file.content_type

        if content_type in ['application/pdf']:
            validated_data['literature_type'] = 'Book'
        elif content_type in ['image/jpeg', 'image/png']:
            validated_data['literature_type'] = 'Image'
        elif content_type in ['text/plain', 'application/msword',
                                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            validated_data['literature_type'] = 'Text'
        elif content_type in ['audio/mpeg', 'audio/mp3']:
            validated_data['literature_type'] = 'Audio'

        return super().create(validated_data)

class HomeworkSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)

    def validate_file(self, value):
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
            literature = LessonLiterature.objects.create(lesson=lesson, **literature_data)
            # Ensure the file is not altered after initial validation
            literature.file = literature_data['file']
            literature.save()

        return lesson

    def update(self, instance, validated_data):
        literatures_data = validated_data.pop('literatures', None)

        if literatures_data is not None:
            for literature_data in literatures_data:
                literature_id = literature_data.get('id')
                if literature_id:
                    literature = LessonLiterature.objects.get(id=literature_id, lesson=instance)
                    for key, value in literature_data.items():
                        if key == 'file':
                            # Ensure the file is not re-validated or altered
                            literature.file = value
                        else:
                            setattr(literature, key, value)
                    literature.save()
                else:
                    literature = LessonLiterature.objects.create(lesson=instance, **literature_data)
                    # Ensure the file is not altered after initial validation
                    literature.file = literature_data['file']
                    literature.save()

        return super().update(instance, validated_data)




class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'lesson_name', 'video_link', 'module']


class ModuleFullSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    lessons = LessonFullSerializer(many=True)

    class Meta:
        model = Module
        fields = ['id', 'module_name', 'lessons']

    def create(self, validated_data):
        lessons_data = validated_data.pop('lessons', [])
        module = Module.objects.create(**validated_data)

        for lesson_data in lessons_data:
            Lesson.objects.create(module=module, **lesson_data)

        return module


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
                    if lesson_id:
                        lesson = Lesson.objects.get(id=lesson_id, module=module)

                        for key, value in lesson_data.items():
                            if key == 'literatures':
                                # Skip file validation here, let LiteratureSerializer handle it
                                literature_ids = [lit['id'] for lit in value if 'id' in lit]
                                lesson.literatures.set(LessonLiterature.objects.filter(id__in=literature_ids))
                            elif key == 'homeworks':
                                self.validate_homeworks(value)  # Validate homeworks
                                homework_ids = [hw['id'] for hw in value if 'id' in hw]
                                lesson.homeworks.set(Homework.objects.filter(id__in=homework_ids))
                            else:
                                setattr(lesson, key, value)
                        lesson.save()

                    else:
                        lesson = Lesson.objects.create(module=module, **lesson_data)
                        literatures = [LessonLiterature.objects.create(**lit) for lit in lesson_data.get('literatures', [])]
                        lesson.literatures.set(literatures)

                        homeworks = [Homework.objects.create(**hw) for hw in lesson_data.get('homeworks', [])]
                        self.validate_homeworks(homeworks)  # Validate homeworks
                        lesson.homeworks.set(homeworks)
            else:
                Module.objects.create(course=instance, **module_data)

        return instance

    def validate_homeworks(self, homeworks):
        allowed_extensions = ['pdf', 'doc', 'docx', 'txt']
        for homework in homeworks:
            file = homework.get('file')
            if file:
                self.validate_file(file, allowed_extensions)

    def validate_file(self, file, allowed_extensions=None):
        if allowed_extensions is None:
            allowed_extensions = ['pdf', 'doc', 'docx', 'txt']

        file_extension = file.name.split('.')[-1].lower()
        mime_type = file.content_type

        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid file extension: {file_extension}")

        allowed_mime_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if mime_type not in allowed_mime_types:
            raise serializers.ValidationError(f"Invalid MIME type: {mime_type}")
