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
        if self.user:
            if self.user.role == 'Psychologist':
                self.type = 'psy'
            elif self.user.role == 'Orientologist':
                self.type = 'ori'
        super(Appointment, self).save(*args, **kwargs)

    def clean(self):
        if Appointment.objects.filter(
            user=self.user,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id).exists():
            raise ValidationError('There is an overlap with another appointment.')
