from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from .forms import AppointmentForm
from .models import Appointment
from django.utils import timezone
from datetime import datetime, timedelta
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
@require_POST
def set_meeting_link(request):
    appointment_id = request.POST.get('appointment_id')
    link = request.POST.get('link')
    # Assuming you have access to the Appointment model
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.link = link
    appointment.save()
    return redirect(reverse('appointments:psychologist_home'))


@login_required
def psychologist_home(request):
    now = timezone.now()  # Current date and time with timezone
    today = now.date()  # Today's date

    appointments_by_day = {}
    for i in range(6):  # Next 6 days including today
        day = today + timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()), timezone.get_current_timezone())
        day_end = timezone.make_aware(datetime.combine(day, datetime.max.time()), timezone.get_current_timezone())

        # Fetch all appointments for the day
        appointments = Appointment.objects.filter(
            date=day
        ).select_related('user').order_by('start_time')

        filtered_appointments = []
        for appointment in appointments:
            start_datetime = timezone.make_aware(datetime.combine(appointment.date, appointment.start_time), timezone.get_current_timezone())
            end_datetime = timezone.make_aware(datetime.combine(appointment.date, appointment.end_time), timezone.get_current_timezone())

            # Include appointment if it ends after the current time
            if end_datetime > now:
                appointment.can_create_meeting = (start_datetime <= now + timedelta(minutes=5) <= end_datetime)
                appointment.meeting_link = appointment.link
                filtered_appointments.append(appointment)

        appointments_by_day[day] = filtered_appointments

    context = {
        'appointments_by_day': appointments_by_day,
        'form': AppointmentForm(),
        'is_superuser_or_psychologist': request.user.is_superuser or (request.user.role == 'Psychologist'),
    }

    return render(request, 'appointments/psychologist_home.html', context)

def appointment_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        print(request.POST.get("date"))
        if form.is_valid():
            new_appointment = form.save(commit=False)
            new_appointment.user = request.user
            new_appointment.save()
            return redirect('appointments:psychologist_home')
        else:
            print(form.errors)
            today = timezone.localdate()
            days = [today + timedelta(days=i) for i in range(6)]
            appointments_by_day = {
                day: Appointment.objects.filter(user=request.user, date=day) for day in days
            }
            return render(request, 'appointments/psychologist_home.html', {
                'appointments_by_day': appointments_by_day,
                'form': form
            })
    else:
        return redirect('appointments:psychologist_home')