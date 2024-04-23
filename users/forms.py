from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
import re

from django.core.exceptions import ValidationError


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

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    re_old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    re_new_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        re_new_password = cleaned_data.get('re_new_password')

        if new_password and re_new_password:
            if new_password != re_new_password:
                raise ValidationError("The new passwords must match.")


class ProfileUpdateForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False)
    class Meta:
        model = get_user_model()
        fields = ['full_name', 'phone_number', 'user_city', 'profile_picture', 'email']

    def __init__(self, *args, **kwargs):
        # Extract the user from kwargs and then call super
        self.user = kwargs.pop('user', None)
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        formatted_phone_number = re.sub(r'\D', '', phone_number)  # Strip non-numeric characters

        if formatted_phone_number and self.user and self.user.phone_number != formatted_phone_number:
            if CustomUser.objects.filter(phone_number=formatted_phone_number).exists():
                raise forms.ValidationError("This phone number is already in use.")
        return formatted_phone_number
