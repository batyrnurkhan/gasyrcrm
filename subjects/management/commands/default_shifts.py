import datetime

from django.core.management.base import BaseCommand

from schedule.models import Shift, ShiftTime


class Command(BaseCommand):
    help = 'Creates data'

    def handle(self, *args, **options):
        first_shift = Shift.objects.create(
            name="1 смена",
            start_time=datetime.time(9, 0, 0, 0),
            end_time=datetime.time(14, 0, 0, 0)
        )
        ShiftTime.objects.create(
            shift=first_shift,
            start_time=datetime.time(9, 0, 0, 0),
            end_time=datetime.time(10, 20, 0, 0),
            date=datetime.date.today()
        )
        ShiftTime.objects.create(
            shift=first_shift,
            start_time=datetime.time(10, 30, 0, 0),
            end_time=datetime.time(11, 50, 0, 0),
            date=datetime.date.today()
        )
        ShiftTime.objects.create(
            shift=first_shift,
            start_time=datetime.time(12, 0, 0, 0),
            end_time=datetime.time(13, 0, 0, 0),
            date=datetime.date.today()
        )
        ShiftTime.objects.create(
            shift=first_shift,
            start_time=datetime.time(13, 0, 0, 0),
            end_time=datetime.time(14, 0, 0, 0),
            date=datetime.date.today()
        )

        second_shift = Shift.objects.create(
            name="2 смена",
            start_time=datetime.time(14, 0, 0, 0),
            end_time=datetime.time(18, 0, 0, 0)
        )
        ShiftTime.objects.create(
            shift=second_shift,
            start_time=datetime.time(14, 0, 0, 0),
            end_time=datetime.time(15, 20, 0, 0),
            date=datetime.date.today()
        )
        ShiftTime.objects.create(
            shift=second_shift,
            start_time=datetime.time(15, 30, 0, 0),
            end_time=datetime.time(16, 50, 0, 0),
            date=datetime.date.today()
        )
        ShiftTime.objects.create(
            shift=second_shift,
            start_time=datetime.time(17, 0, 0, 0),
            end_time=datetime.time(18, 0, 0, 0),
            date=datetime.date.today()
        )

        third_shift = Shift.objects.create(
            name="3 смена",
            start_time=datetime.time(16, 0, 0, 0),
            end_time=datetime.time(20, 0, 0, 0)
        )
        ShiftTime.objects.create(
            shift=third_shift,
            start_time=datetime.time(16, 0, 0, 0),
            end_time=datetime.time(17, 20, 0, 0),
            date=datetime.date.today()
        )
        ShiftTime.objects.create(
            shift=third_shift,
            start_time=datetime.time(17, 30, 0, 0),
            end_time=datetime.time(18, 50, 0, 0),
            date=datetime.date.today()
        )
        ShiftTime.objects.create(
            shift=third_shift,
            start_time=datetime.time(19, 0, 0, 0),
            end_time=datetime.time(20, 0, 0, 0),
            date=datetime.date.today()
        )
        print("Done")