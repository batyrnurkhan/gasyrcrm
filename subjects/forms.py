from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import VolunteerChannel, Grade, Achievement, StudentAchievement, Subject
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
    teacher = forms.ChoiceField()
    students = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role='Student'), widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = Lesson_crm2
        fields = ['group_name', 'subject', 'group_template', 'teacher', 'students', 'time_slot', 'google_meet_link']
        widgets = {
            'time_slot': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(LessonForm, self).__init__(*args, **kwargs)
        self.teachers_info = [(e.id, e.full_name, e.profile_picture.url if e.profile_picture else '') for e in CustomUser.objects.filter(role="Teacher")]
        self.subjects_info = [(e.id, e.name, e.image.url if e.image else '') for e in Subject.objects.all()]
        self.group_templates_info = [('', 'Пустой шаблон', {})] + [(i.id, i.name, {e.id: e.full_name for e in CustomUser.objects.filter(group_template=i)}) for i in GroupTemplate.objects.all()]

        self.fields['teacher'].choices = [(e.id, e.full_name) for e in CustomUser.objects.filter(role="Teacher")]
        self.fields['subject'].choices = [(e.id, e.name) for e in Subject.objects.all()]

    def clean(self):
        print(list(self.fields['group_template'].choices))
        cleaned_data = super().clean()
        group_template = cleaned_data.get('group_template', None)
        if not group_template:
            cleaned_data['group_template'] = group_template = None
        print(list(cleaned_data))
        print(cleaned_data['group_template'])
        teacher = CustomUser.objects.get(id=cleaned_data.get('teacher'))
        cleaned_data['teacher'] = teacher
        students = cleaned_data.get('students')
        time_slot = cleaned_data.get('time_slot')
        print(students)

        # Validate that no student in the group template has a conflicting lesson
        if group_template and time_slot:
            students_in_template = group_template.students.all()
            overlapping_lessons = Lesson_crm2.objects.filter(
                group_template__students__in=students_in_template,
                time_slot=time_slot
            ).distinct()

            if overlapping_lessons.exists():
                raise ValidationError("Студент из шаблона уже имеет урок в указанном времени.")

        # Validate that no individual student has a conflicting lesson
        if students and time_slot:
            for student in students:
                overlapping_lessons = Lesson_crm2.objects.filter(
                    students=student,
                    time_slot=time_slot
                ).distinct()

                if overlapping_lessons.exists():
                    raise ValidationError(f"Студент {student.full_name} уже имеет урок в этом промежутке времени.")

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
                    self.add_error(field.name, ValidationError("Неправильная оценка, оценка не может быть выше максимальной оцени."))
        return cleaned_data

    def save_grades(self, lesson, date_assigned, file):
        max_grade = self.cleaned_data['max_grade']
        for student, field in self.student_fields:
            grade_value = self.cleaned_data.get(field.name)
            if grade_value is not None:
                grade, created = Grade.objects.update_or_create(
                    student=student,
                    lesson=lesson,
                    date_assigned=date_assigned,
                    defaults={'grade': grade_value, 'max_grade': max_grade}
                )
                if file:
                    grade.file = file
                    grade.save()

class FileUploadForm(forms.Form):
    task_id = forms.IntegerField(widget=forms.HiddenInput())
    file = forms.FileField(label="Upload your work")

class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['name', 'difficulty']

class StudentAchievementForm(forms.ModelForm):
    class Meta:
        model = StudentAchievement
        fields = ['student', 'achievement']
        widgets = {
            'student': forms.HiddenInput(),
            'achievement': forms.HiddenInput(),
        }