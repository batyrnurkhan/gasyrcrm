from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'date', 'start_time', 'end_time', 'link', 'is_booked', 'user']

    def validate(self, data):
        # Additional custom validation can go here, such as checking for overlapping appointments.
        return data

    def create(self, validated_data):
        appointment = Appointment.objects.create(**validated_data)
        return appointment

    def update(self, instance, validated_data):
        instance.link = validated_data.get('link', instance.link)
        instance.is_booked = validated_data.get('is_booked', instance.is_booked)
        instance.save()
        return instance