from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
import re

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('full_name', 'phone_number', 'user_city')

CustomUser = get_user_model()

class CustomUserAuthenticationForm(AuthenticationForm):
    # Ensure the field name matches your custom user model's USERNAME_FIELD
    phone_number = forms.CharField(label="Phone Number", required=True)

    def __init__(self, *args, **kwargs):
        super(CustomUserAuthenticationForm, self).__init__(*args, **kwargs)
        # Remove the default 'username' field
        del self.fields['username']
        # Add or modify fields as necessary
        self.fields['phone_number'] = forms.CharField(label="Phone Number", required=True)

class AccessCodeForm(forms.Form):
    login_code = forms.CharField(max_length=10, label="Login Code", help_text="Enter the user's login code to grant access.", required=True)
