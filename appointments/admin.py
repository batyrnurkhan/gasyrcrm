from django.contrib import admin
from .models import Appointment
# Register your models here.

@admin.register(Appointment)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'date']
