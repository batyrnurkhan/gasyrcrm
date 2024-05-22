from django.contrib import admin

# Register your models here.
from .models import Test, Question, Answer, Course, Module, Lesson, LessonLiterature, TestSubmission

class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id','content_object', 'title')  # Add 'id' to display in the admin interface

admin.site.register(Test, TestAdmin)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(LessonLiterature)
admin.site.register(TestSubmission)
