from django.contrib import admin

from .models import Subject, GroupTemplate, Lesson_crm2, VolunteerChannel, Grade, Task

# Register your models here.
admin.site.register(Subject)
admin.site.register(GroupTemplate)

admin.site.register(VolunteerChannel)
admin.site.register(Grade)
admin.site.register(Task)

@admin.register(Lesson_crm2)
class OLesson_crm2Admin(admin.ModelAdmin):
    list_display = ['id', 'group_name']