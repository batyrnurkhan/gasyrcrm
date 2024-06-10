from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import VolunteerChannel, Grade
from users.models import CustomUser
from .models import Task, Lesson_crm2, GroupTemplate


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'deadline', 'file']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')
        }


class LessonForm(ModelForm):
    class Meta:
        model = Lesson_crm2
        fields = ['group_name', 'subject', 'group_template', 'teacher', 'time_slot']
        widgets = {
            'time_slot': forms.HiddenInput()  # Assuming you handle the time_slot input elsewhere in your logic
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['subject'].widget.attrs.update({'class': 'form-control'})
        self.fields['group_template'].widget.attrs.update({'class': 'form-control'})
        self.fields['teacher'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        group_template = cleaned_data.get('group_template')
        teacher = cleaned_data.get('teacher')
        time_slot = cleaned_data.get('time_slot')

        # Validate that no student in the group template has a conflicting lesson
        if group_template and time_slot:
            students = group_template.students.all()
            overlapping_lessons = Lesson_crm2.objects.filter(
                group_template__students__in=students,
                time_slot=time_slot
            ).distinct()

            if overlapping_lessons.exists():
                raise ValidationError("A student in the selected group template already has a lesson during this time slot.")

        # Check if the selected teacher is already booked for the given time slot
        if teacher and time_slot:
            if Lesson_crm2.objects.filter(teacher=teacher, time_slot=time_slot).exists():
                raise ValidationError(f"Учитель уже занят в это время: {teacher.full_name} has a lesson at {time_slot.start_time} to {time_slot.end_time}.")

        return cleaned_data


class GroupTemplateForm(forms.ModelForm):
    class Meta:
        model = GroupTemplate
        fields = ['name']


class UserSearchForm(forms.Form):
    search = forms.CharField(label='Search by name or phone number', max_length=100, required=False)

    def search_users(self):
        search_term = self.cleaned_data['search']
        # Fetch top 10 students by name, alphabetically
        return CustomUser.objects.filter(role='Student', full_name__icontains=search_term).order_by('full_name')[:10]


class VolunteerChannelForm(forms.ModelForm):
    class Meta:
        model = VolunteerChannel
        fields = ['name', 'description']

    selected_students = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role='Student'),
        required=False,
        widget=forms.HiddenInput()
    )

    def clean_selected_students(self):
        user_ids = self.cleaned_data.get('selected_students')
        return CustomUser.objects.filter(id__in=user_ids)


class GradeForm(forms.Form):
    max_grade = forms.IntegerField(label="Maximum Grade")
    date_assigned = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    file = forms.FileField(label="Upload File", required=False)

    def __init__(self, *args, **kwargs):
        students = kwargs.pop('students', None)
        super().__init__(*args, **kwargs)
        self.student_fields = []
        if students:
            for student in students:
                field_name = f'grade_{student.id}'
                self.fields[field_name] = forms.IntegerField(label=f'Grade for {student.full_name}', required=False)
                self.student_fields.append((student, self[field_name]))

    def clean(self):
        cleaned_data = super().clean()
        max_grade = cleaned_data.get('max_grade')
        if max_grade is not None:
            for student, field in self.student_fields:
                grade = cleaned_data.get(field.name)
                if grade is not None and grade > max_grade:
                    self.add_error(field.name, ValidationError("Incorrect grade, it cannot be higher than the maximum grade."))

        return cleaned_data

    def save_grades(self, lesson, date_assigned, file):
        grades = []
        max_grade = self.cleaned_data['max_grade']
        for student, field in self.student_fields:
            if self.cleaned_data[field.name]:
                grade = Grade(
                    student=student,
                    lesson=lesson,
                    grade=self.cleaned_data[field.name],
                    max_grade=max_grade,
                    date_assigned=date_assigned,
                    file=file
                )
                grades.append(grade)
        Grade.objects.bulk_create(grades)


class FileUploadForm(forms.Form):
    task_id = forms.IntegerField(widget=forms.HiddenInput())
    file = forms.FileField(label="Upload your work")
