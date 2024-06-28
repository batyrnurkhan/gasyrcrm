from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView
from django.http import HttpResponseForbidden


from django.shortcuts import render

from users.models import CustomUser
from .models import Shift, ShiftTime
from django.http import JsonResponse
from subjects.models import Lesson_crm2

def get_shifts_for_day(request, day):
    day_name_map = {
        'monday': 2,
        'tuesday': 3,
        'wednesday': 4,
        'thursday': 5,
        'friday': 6,
        'saturday': 7
    }

    weekday = day_name_map.get(day.lower())

    if weekday is None:
        return JsonResponse({'error': 'Invalid day'}, status=400)

    shift_times = ShiftTime.objects.filter(date__week_day=weekday)
    shift_data = []

    for shift_time in shift_times:
        lessons = Lesson_crm2.objects.filter(time_slot=shift_time)
        lesson_data = [{
            'mentor': lesson.mentor.full_name,
            'teacher': lesson.teacher.full_name if lesson.teacher else 'No teacher assigned',
            'group_name': lesson.group_name,
            'subject': lesson.subject.name,
            'students': [student.full_name for student in lesson.students.all()],
            'time_slot': f"{lesson.time_slot.start_time.strftime('%H:%M')} - {lesson.time_slot.end_time.strftime('%H:%M')}",
            'google_meet_link': lesson.google_meet_link,
        } for lesson in lessons]

        shift_data.append({
            'shift_name': shift_time.shift.name,
            'start_time': shift_time.start_time.strftime('%H:%M'),
            'end_time': shift_time.end_time.strftime('%H:%M'),
            'lessons': lesson_data
        })

    return JsonResponse(shift_data, safe=False)
def shifts_view(request):
    # Fetch all shifts and related data in an optimized manner
    shifts = Shift.objects.prefetch_related(
        'times__lessons',
        'times__lessons__teacher',
        'times__lessons__subject',
        'times__lessons__group_template'
    ).all()

    if not shifts:
        print("No shifts found.")
    else:
        print(f"Found {len(shifts)} shifts.")

    return render(request, 'schedule/shifts.html', {'shifts': shifts, 'page': 'schedule', 'students': CustomUser.objects.filter(role="Student")})