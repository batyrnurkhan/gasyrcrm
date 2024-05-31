from django.shortcuts import render
from datetime import datetime, timedelta
from .models import Appointment

def week_view(request):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Ensure Monday is day 0
    dates_of_week = [start_of_week + timedelta(days=i) for i in range(6)]  # Get Monday to Saturday

    context = {
        'dates_of_week': dates_of_week,
    }
    return render(request, 'appointments/week_view.html', context)

def appointments_for_day(request, year, month, day):
    date = datetime(year, month, day).date()
    appointments = Appointment.objects.filter(date=date)
    context = {
        'appointments': appointments,
        'date': date  # Pass the date to use in the template
    }
    return render(request, 'appointments/appointments_for_day.html', context)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Appointment
from .serializers import AppointmentSerializer

class AppointmentListCreateAPIView(APIView):
    def get(self, request):
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentSetLinkAPIView(APIView):
    def patch(self, request, pk):
        appointment = Appointment.objects.get(pk=pk)
        serializer = AppointmentSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def create_appointment_view(request):
    return render(request, 'appointments/create_appointment.html')

def set_link_view(request):
    return render(request, 'appointments/set_link.html')