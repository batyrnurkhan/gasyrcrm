from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['date', 'start_time', 'end_time', 'link', 'is_booked', 'user']

    def validate(self, data):
        appointment = Appointment(**data)

        if 'user' not in data:
            raise serializers.ValidationError("User must be specified.")
        appointment.user = self.context['request'].user

        try:
            appointment.clean()
        except ValidationError as e:
            raise serializers.ValidationError({'non_field_errors': e.messages})

        return data

class AppointmentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['link']  # Only include the link field for updates

    def update(self, instance, validated_data):
        instance.link = validated_data.get('link', instance.link)
        instance.save()
        return instance