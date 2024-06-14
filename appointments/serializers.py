from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'date', 'start_time', 'end_time', 'link', 'is_booked', 'user', 'user_full_name', 'description']
        extra_kwargs = {
            'user': {'read_only': True},
            'description': {'required': False}  # Set to false to allow the validate method to handle the logic
        }

    def get_user_full_name(self, obj):
        return obj.user.full_name if obj.user else None

    def validate(self, data):
        # Ensure a description is provided when booking an appointment
        if data.get('is_booked') and not data.get('description'):
            raise serializers.ValidationError("A description must be provided when booking an appointment.")

        # Check for overlapping appointments
        if self.instance:  # Check if it is an update
            qs = Appointment.objects.filter(
                user=data.get('user', self.instance.user),
                date=data.get('date', self.instance.date),
                start_time__lt=data.get('end_time', self.instance.end_time),
                end_time__gt=data.get('start_time', self.instance.start_time)
            ).exclude(id=self.instance.id)
        else:  # It's a new appointment
            qs = Appointment.objects.filter(
                user=data.get('user'),
                date=data.get('date'),
                start_time__lt=data.get('end_time'),
                end_time__gt=data.get('start_time')
            )

        if qs.exists():
            raise serializers.ValidationError('There is an overlap with another appointment.')

        return data
class AppointmentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['link']  # Only include the link field for updates

    def update(self, instance, validated_data):
        instance.link = validated_data.get('link', instance.link)
        instance.save()
        return instance