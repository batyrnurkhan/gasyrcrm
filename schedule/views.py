from django.shortcuts import render
from django.views.decorators.http import require_GET
from .models import Shift, ShiftTime
import calendar


@require_GET
def shifts_view(request):
    shifts = Shift.objects.all()
    return render(request, 'schedule/shifts.html', {'shifts': shifts, 'page': 'schedule'})


@require_GET
def lessons_by_day_view(request, day):
    day_index = list(calendar.day_name).index(day)
    shifts = Shift.objects.all()
    shift_times = ShiftTime.objects.filter(date__week_day=day_index + 1).prefetch_related(
        'lessons',
        'lessons__teacher',
        'lessons__subject',
        'lessons__group_template'
    )
    shift_times_dict = {}
    for shift_time in shift_times:
        if shift_time.shift_id not in shift_times_dict:
            shift_times_dict[shift_time.shift_id] = []
        shift_times_dict[shift_time.shift_id].append(shift_time)

    return render(request, 'schedule/lessons_list.html',
                  {'shifts': shifts, 'shift_times_dict': shift_times_dict, 'selected_day': day})
