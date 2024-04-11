from django import forms
from .models import Course, Module, Lesson, LessonLiterature, Test, Question, Answer


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_name', 'mini_description', 'course_picture', 'big_description', 'course_time', 'course_difficulty', 'full_description']

class CourseFormStep1(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_name', 'mini_description', 'course_picture']

class CourseFormStep2(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['big_description', 'course_time', 'course_difficulty', 'full_description']

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['module_name']

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['lesson_name', 'video_link']

class LessonLiteratureForm(forms.ModelForm):
    class Meta:
        model = LessonLiterature
        fields = ['literature_name', 'literature_type', 'file']

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']