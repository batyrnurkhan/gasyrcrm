import re

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group
from django.core.validators import EmailValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number is mandatory')

        # Remove all non-digit characters from phone_number before saving
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
    role = models.CharField(max_length=13, choices=ROLE_CHOICES, blank=True, null=True,
                            default='Anonymous')
    login_code = models.CharField(max_length=7, blank=True, null=True, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    has_access = models.BooleanField(default=False)
    email = models.EmailField(max_length=255, unique=True, validators=[EmailValidator()], null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'user_city']

    def save(self, *args, **kwargs):
        if self.role == 'Teacher':
            self.has_access = True
        super(CustomUser, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

