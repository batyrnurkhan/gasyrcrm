from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['date', 'start_time', 'end_time', 'link', 'is_booked', 'user']

class AppointmentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['link']  # Only include the link field for updates

    def update(self, instance, validated_data):
        instance.link = validated_data.get('link', instance.link)
        instance.save()
        return instance