from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.name} from {self.start_time} to {self.end_time}"

class ShiftTime(models.Model):
    shift = models.ForeignKey(Shift, related_name='times', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField()

    def day_of_week(self):
        return self.date.strftime('%A')  # Returns the full weekday name

    def __str__(self):
        return f"{self.shift.name} on {self.date} - {self.start_time} to {self.end_time}"