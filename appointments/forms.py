from django import forms
from django.forms import ModelForm
from .models import Appointment

class AppointmentForm(ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")

        return cleaned_data