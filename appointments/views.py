from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta

from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from rest_framework.permissions import IsAuthenticated

from .models import Appointment

@login_required
def week_view(request):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Ensure Monday is day 0
    dates_of_week = [start_of_week + timedelta(days=i) for i in range(6)]  # Get Monday to Saturday

    context = {
        'dates_of_week': dates_of_week,
        'user_role': request.user.role,
    }
    return render(request, 'appointments/week_view.html', context)


def appointments_for_day_api(request, type, year, month, day):
    date = datetime(year, month, day).date()
    appointments = Appointment.objects.filter(date=date, type=type).select_related('user')
    appointment_list = [
        {
            'id': appointment.id,
            'start_time': appointment.start_time.strftime('%H:%M'),
            'end_time': appointment.end_time.strftime('%H:%M'),
            'is_booked': appointment.is_booked,
            'link': appointment.link,
            'user_full_name': appointment.user.full_name if appointment.is_booked else None,
            'user_profile_pic_url': appointment.user.profile_picture.url if appointment.is_booked and appointment.user.profile_picture else None
        }
        for appointment in appointments
    ]
    return JsonResponse({'appointments': appointment_list, 'date': date.strftime("%Y-%m-%d")})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Appointment
from .serializers import AppointmentSerializer, AppointmentLinkSerializer


class AppointmentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()  # Automatically use the logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentSetLinkAPIView(APIView):
    def patch(self, request, pk):
        appointment = Appointment.objects.get(pk=pk)
        serializer = AppointmentLinkSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentBookAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            if appointment.is_booked:
                return Response({"error": "This appointment is already booked."}, status=status.HTTP_400_BAD_REQUEST)

            appointment.is_booked = True
            appointment.user = request.user
            appointment.save()
            return redirect('appointments:success-appointment')  # Redirect to success page
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment does not exist."}, status=status.HTTP_404_NOT_FOUND)


@login_required
def success_appointment_view(request):
    latest_appointment = Appointment.objects.filter(user=request.user, is_booked=True).order_by('-date', '-start_time').first()
    if not latest_appointment:
        return redirect('subjects:psy-appointment')  # Redirect back if no appointment

    context = {
        'user_full_name': request.user.full_name,
        'user_profile_pic_url': request.user.profile_picture.url if request.user.profile_picture else None,
        'appointment_date': latest_appointment.date.strftime("%d %B %Y"),
        'appointment_time': latest_appointment.start_time.strftime("%H:%M"),
        'appointment_link': latest_appointment.link,  # Ensure this is included
        'appointment': latest_appointment
    }

    return render(request, 'subjects/appointment/success-appointment.html', context)


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)

    if request.method == 'POST':
        appointment.is_booked = False
        appointment.user = None
        appointment.save()
        messages.success(request, "Your appointment has been successfully cancelled.")
        return redirect('subjects:psy-appointment')  # Redirect to the appointment view or another relevant page
    else:
        # Prevent accidental GET requests from cancelling the appointment
        messages.error(request, "Invalid request method.")
        return redirect('appointments:success-appointment')