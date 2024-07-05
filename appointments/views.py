from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta

from django.urls import reverse
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from rest_framework.permissions import IsAuthenticated

from .models import Appointment
from django.utils.timezone import now

@login_required
def week_view(request):
    # Delete expired appointments before rendering the week view
    expired_appointments = Appointment.objects.filter(date__lt=now().date())
    expired_appointments.delete()

    week_offset = int(request.GET.get('week_offset', 0))
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    dates_of_week = [start_of_week + timedelta(days=i) for i in range(7)]

    context = {
        'dates_of_week': dates_of_week,
        'user_role': request.user.role,  # Pass user role to the context
        'week_offset': week_offset,
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
from django.core.exceptions import ValidationError


class AppointmentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()  # Automatically use the logged-in user
                messages.success(request._request, 'Appointment created successfully.')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                error_message = ' '.join([str(err) for err in e])
                messages.error(request._request, f'Ошибка: {error_message}')
                return Response({'errors': error_message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentSetLinkAPIView(APIView):
    def patch(self, request, pk):
        appointment = Appointment.objects.get(pk=pk)
        serializer = AppointmentLinkSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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
            success_url = reverse('appointments:success-appointment')
            return Response({"success": True, "date": str(appointment.date), "redirect_url": success_url}, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def success_appointment_view(request):
    latest_appointment = Appointment.objects.filter(user=request.user, is_booked=True).order_by('-date', '-start_time').first()
    if not latest_appointment:
        return redirect('subjects:psy-appointment')

    context = {
        'user_full_name': request.user.full_name,
        'user_profile_pic_url': request.user.profile_picture.url if request.user.profile_picture else None,
        'appointment_date': latest_appointment.date.strftime("%d %B %Y"),
        'appointment_time': latest_appointment.start_time.strftime("%H:%M"),
        'appointment_link': latest_appointment.link,
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
        return redirect('subjects:psy-appointment')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('appointments:success-appointment')