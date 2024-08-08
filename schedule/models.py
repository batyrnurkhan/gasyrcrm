from django.db import models
from django.conf import settings

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.name} from {self.start_time} to {self.end_time}"

class ShiftTime(models.Model):
    WEEKDAYS = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    shift = models.ForeignKey(Shift, related_name='times', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    weekday = models.IntegerField(choices=WEEKDAYS)

    def __str__(self):
        return f"{self.shift.name} on {self.get_weekday_display()} - {self.start_time} to {self.end_time}"
