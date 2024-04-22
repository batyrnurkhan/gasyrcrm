# appointments/management/commands/generate_slots.py

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from appointments.models import Appointment
import pytz


class Command(BaseCommand):
    help = 'Generates appointment slots for the next week'

    def handle(self, *args, **options):
        self.generate_appointment_slots()

    def generate_appointment_slots(self):
        start_date = datetime.now().date()  # Consider adjusting to the next week's Monday
        while start_date.weekday() != 0:  # Find the next Monday
            start_date += timedelta(days=1)

        # Define time slots
        time_slots = [
            ('10:00', '11:30'),
            ('11:45', '13:15'),
            ('13:30', '15:00'),
            ('15:15', '16:45'),
            ('17:00', '18:30'),
        ]

        # Generate slots for a week Monday to Saturday
        for i in range(6):  # 0 to 5, Monday to Saturday
            day = start_date + timedelta(days=i)
            for start, end in time_slots:
                Appointment.objects.create(
                    date=day,
                    start_time=datetime.strptime(start, '%H:%M').time(),
                    end_time=datetime.strptime(end, '%H:%M').time(),
                    is_booked=False
                )

        self.stdout.write(self.style.SUCCESS('Successfully generated slots for a week'))
