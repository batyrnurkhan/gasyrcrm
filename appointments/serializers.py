from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['date', 'start_time', 'end_time', 'link', 'is_booked', 'user', 'user_full_name']
        extra_kwargs = {
            'user': {'read_only': True}
        }

    def get_user_full_name(self, obj):
        # Ensure you return the actual attribute that holds the user's full name
        return obj.user.full_name if obj.user else None

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            data['user'] = request.user
        else:
            raise serializers.ValidationError("User must be specified.")

        appointment = Appointment(**data)

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