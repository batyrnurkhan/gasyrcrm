from django import forms

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