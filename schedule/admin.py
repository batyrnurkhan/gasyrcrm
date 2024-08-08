from django.contrib import admin
from .models import Shift, ShiftTime

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time']

@admin.register(ShiftTime)
class ShiftTimeAdmin(admin.ModelAdmin):
    list_display = ['shift', 'start_time', 'end_time', 'weekday']
    list_filter = ['shift']
