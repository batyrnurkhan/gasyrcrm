import re
from datetime import timedelta, date

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import EmailValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number is mandatory')
        formatted_phone_number = re.sub(r'\D', '', phone_number)
        user = self.model(phone_number=formatted_phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('Anonymous', 'Anonymous'),
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Mentor', 'Mentor'),
        ('Psychologist', 'Psychologist'),
        ('Orientologist', 'Orientologist'),
    )

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=22, unique=True)
    user_city = models.CharField(max_length=100, choices=[(city, city) for city in
                                                          ['Astana', 'Almaty', 'Shymkent', 'Karaganda', 'Aktobe',
                                                           'Taraz', 'Pavlodar', 'Oskemen', 'Semey', 'Atyrau']])
    role = models.CharField(max_length=13, choices=ROLE_CHOICES, blank=True, null=True, default='Anonymous')
    login_code = models.CharField(max_length=7, blank=True, null=True, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    has_access = models.BooleanField(default=False)
    email = models.EmailField(max_length=255, unique=True, validators=[EmailValidator()], null=True, blank=True)

    last_opened_content_id = models.PositiveIntegerField(null=True, blank=True)

    admission_country = models.CharField(max_length=255, verbose_name='Страна поступление', blank=True, null=True)
    education_class = models.CharField(max_length=100, verbose_name='Класс обучения', blank=True, null=True)
    registration_date = models.DateField(verbose_name='Дата регистрации', default=date.today, editable=True)
    contract_end_date = models.DateField(verbose_name='Дата окончание договора', blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'user_city']

    def save(self, *args, **kwargs):
        # If registration_date is set and contract_end_date is not set, calculate and set it
        if self.registration_date and not self.contract_end_date:
            self.contract_end_date = self.registration_date + timedelta(days=120)  # Approximately 4 months

        # Set has_access to True if the user is a Teacher
        if self.role == 'Teacher':
            self.has_access = True

        # Call the parent save method to ensure the instance is saved correctly
        super(CustomUser, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

