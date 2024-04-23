# appointments/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import Appointment
from django.contrib.auth.decorators import login_required

@login_required
def list_appointments(request):
    appointments = Appointment.objects.filter(is_booked=False).order_by('date', 'start_time')
    return render(request, 'appointments/list.html', {'appointments': appointments})

@login_required
def book_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        appointment.is_booked = True
        appointment.user = request.user
        appointment.save()
        return redirect('appointments:list_appointments')
    return render(request, 'appointments/book.html', {'appointment': appointment})
