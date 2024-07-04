from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


class Appointment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    link = models.URLField(blank=True, null=True)
    is_booked = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        return f"{self.date} from {self.start_time} to {self.end_time}"

    def save(self, *args, **kwargs):
        self.clean()  # Ensure clean is called before saving
        super(Appointment, self).save(*args, **kwargs)

    def clean(self):
        # Check for overlapping appointments for the same type on the same date
        overlapping_appointments = Appointment.objects.filter(
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            type=self.type
        ).exclude(id=self.id)

        if overlapping_appointments.exists():
            raise ValidationError('Вы не можете создавать пересекающие графики.')

        super(Appointment, self).clean()
