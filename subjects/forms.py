from django import forms
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

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson_crm2
        fields = ['group_name', 'subject', 'group_template', 'teacher', 'time_slot']
        widgets = {
            'time_slot': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['subject'].widget.attrs.update({'class': 'form-control'})
        self.fields['group_template'].widget.attrs.update({'class': 'form-control'})
        self.fields['teacher'].widget.attrs.update({'class': 'form-control'})


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
        fields = ['name', 'description', 'users']

class GradeForm(forms.Form):
    max_grade = forms.IntegerField(label="Maximum Grade")
    date_assigned = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        students = kwargs.pop('students', None)
        super().__init__(*args, **kwargs)
        self.student_fields = []
        if students:
            for student in students:
                field_name = f'grade_{student.id}'
                self.fields[field_name] = forms.IntegerField(label=f'Grade for {student.full_name}', required=False)
                self.student_fields.append((student, self[field_name]))

    def save_grades(self, lesson, date_assigned):
        grades = []
        for student, field in self.student_fields:
            if self.cleaned_data[field.name]:
                grades.append(Grade(
                    student=student,
                    lesson=lesson,
                    grade=self.cleaned_data[field.name],
                    date_assigned=date_assigned
                ))
        Grade.objects.bulk_create(grades)