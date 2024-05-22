from django.contrib import admin

from .models import Subject, GroupTemplate, Lesson_crm2, VolunteerChannel, Grade, Task

# Register your models here.
admin.site.register(Subject)
admin.site.register(GroupTemplate)
admin.site.register(Lesson_crm2)
admin.site.register(VolunteerChannel)
admin.site.register(Grade)
admin.site.register(Task)