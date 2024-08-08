from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from .models import Shift, ShiftTime
from subjects.models import Lesson_crm2

def get_shifts_for_day(request, day):
    day_name_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }

    weekday = day_name_map.get(day.lower())
    if weekday is None:
        return JsonResponse({'error': 'Invalid day'}, status=400)

    shift_times = ShiftTime.objects.filter(weekday=weekday)

    shift_data = []
    for shift_time in shift_times:
        lessons = Lesson_crm2.objects.filter(time_slot=shift_time)
        lesson_data = [{
            'mentor': lesson.mentor.full_name,
            'teacher': lesson.teacher.full_name if lesson.teacher else 'No teacher assigned',
            'group_name': lesson.group_name,
            'subject': lesson.subject.name,
            'students': [student.full_name for student in lesson.students.all()],
            'time_slot': f"{shift_time.start_time.strftime('%H:%M')} - {shift_time.end_time.strftime('%H:%M')}",
            'google_meet_link': lesson.google_meet_link,
        } for lesson in lessons]

        shift_data.append({
            'shift_name': shift_time.shift.name,
            'start_time': shift_time.start_time.strftime('%H:%M'),
            'end_time': shift_time.end_time.strftime('%H:%M'),
            'lessons': lesson_data,
            'time_id': shift_time.id
        })

    if not shift_data:
        shifts = Shift.objects.all()
        for shift in shifts:
            times = shift.times.filter(weekday=weekday)
            time_data = [{
                'start_time': time.start_time.strftime('%H:%M'),
                'end_time': time.end_time.strftime('%H:%M'),
                'lessons': [],
                'time_id': time.id
            } for time in times]
            shift_data.append({
                'shift_name': shift.name,
                'times': time_data
            })

    html = render_to_string('schedule/partials/shifts_content.html', {'shifts': shift_data})
    return JsonResponse({'html': html}, safe=False)


@login_required
def shifts_view(request):
    shifts = Shift.objects.prefetch_related(
        'times',
    ).all()

    return render(request, 'schedule/shifts.html', {'shifts': shifts})
