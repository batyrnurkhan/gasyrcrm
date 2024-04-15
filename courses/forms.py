from django import forms
from .models import Course, Module, Lesson, LessonLiterature, Test, Question, Answer
from users.models import CustomUser

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
        fields = ['title']  # Include other relevant fields


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']

class AddStudentForm(forms.Form):
    search_query = forms.CharField(label='Search by name or phone number', max_length=100)

    def clean_search_query(self):
        # Clean and return the search query, maybe trim whitespaces
        return self.cleaned_data['search_query'].strip()