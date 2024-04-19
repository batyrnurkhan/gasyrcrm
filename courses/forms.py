from django import forms
from .models import Course, Module, Lesson, LessonLiterature, Test, Question, Answer
from users.models import CustomUser

class CourseForm(forms.ModelForm):
    course_difficulty = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=Course.DIFFICULTY_CHOICES,
    )

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
    image = forms.ImageField(required=False)
    audio = forms.FileField(required=False)

    class Meta:
        model = Question
        fields = ['text', 'question_type', 'image', 'audio']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']

from django.core.validators import RegexValidator


# class AddStudentForm(forms.Form):
#     search_query = forms.CharField(
#         label='Search by name',
#         max_length=100,
#         required=False,
#         help_text='Enter the full name of the student.'
#     )
#     phone_number = forms.CharField(
#         label='Search by phone number',
#         max_length=15,
#         required=False,
#         help_text='Enter the phone number of the student.'
#     )
#     login_code = forms.CharField(
#         label='Search by login code',
#         max_length=7,
#         required=False,
#         help_text='Enter the login code of the student.'
#     )
#
#     def clean(self):
#         cleaned_data = super().clean()
#         search_query = cleaned_data.get('search_query')
#         phone_number = cleaned_data.get('phone_number')
#         login_code = cleaned_data.get('login_code')
#
#         if not any([search_query, phone_number, login_code]):
#             raise forms.ValidationError("Please provide at least one search criteria.")
#
#         if sum([bool(search_query), bool(phone_number), bool(login_code)]) > 1:
#             raise forms.ValidationError("Please search by only one criterion at a time.")
#
#         return cleaned_data

class AddStudentForm(forms.Form):
    login_code = forms.CharField(
        label='Search by login code',
        max_length=7,
        required=False,
        help_text='Enter the login code of the student.'
    )

    def clean(self):
        cleaned_data = super().clean()
        login_code = cleaned_data.get('login_code')

        if not login_code:
            raise forms.ValidationError("Please provide the login code.")

        return cleaned_data