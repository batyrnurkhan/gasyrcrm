from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta

from rest_framework.permissions import IsAuthenticated

from .models import Appointment

def week_view(request):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Ensure Monday is day 0
    dates_of_week = [start_of_week + timedelta(days=i) for i in range(6)]  # Get Monday to Saturday

    context = {
        'dates_of_week': dates_of_week,
    }
    return render(request, 'appointments/week_view.html', context)



def appointments_for_day_api(request, year, month, day):
    date = datetime(year, month, day).date()
    appointments = Appointment.objects.filter(date=date)
    appointment_list = [model_to_dict(appointment) for appointment in appointments]  # Convert queryset to list of dicts
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
            return Response(
                {"success": "Appointment booked successfully.", "date": appointment.date.strftime("%Y-%m-%d")},
                status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment does not exist."}, status=status.HTTP_404_NOT_FOUND)
