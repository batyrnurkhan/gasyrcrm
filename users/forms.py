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
                raise ValidationError("Пароли должны совпадать")


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
            raise forms.ValidationError("Почта уже используется")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        formatted_phone_number = re.sub(r'\D', '', phone_number)  # Strip non-numeric characters

        if formatted_phone_number and self.user and self.user.phone_number != formatted_phone_number:
            if CustomUser.objects.filter(phone_number=formatted_phone_number).exists():
                raise forms.ValidationError("Этот номер телефона уже используется")
        return formatted_phone_number


class TeacherCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=True)
    last_name = forms.CharField(max_length=255, required=True)
    phone_number = forms.CharField(max_length=22, required=True)  # Make sure to capture this in the form fields if you want to normalize it in the form

    class Meta:
        model = CustomUser
        fields = ['phone_number']

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        normalized_phone_number = re.sub(r'\D', '', phone_number)
        if not normalized_phone_number.startswith('7'):
            normalized_phone_number = '7' + normalized_phone_number
        return normalized_phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}"
        user.role = 'Teacher'
        user.user_city = "Almaty"  # Default city
        password = CustomUser.objects.make_random_password()
        user.set_password(password)
        if commit:
            user.save()
        return user, password

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['admission_country', 'education_class', 'registration_date', 'contract_end_date']
        widgets = {
            'admission_country': forms.TextInput(attrs={'class': 'form-control'}),
            'education_class': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }