# appointments/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

class Appointment(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    link = models.URLField(blank=True)  # allow empty links
    is_booked = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)  # Optional description field

    def __str__(self):
        return f"{self.date} from {self.start_time} to {self.end_time}"

    def clean(self):
        # Validate to avoid overlapping appointments
        if Appointment.objects.filter(
            user=self.user,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id).exists():
            raise ValidationError('There is an overlap with another appointment.')


