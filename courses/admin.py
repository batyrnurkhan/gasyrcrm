from django.contrib import admin

# Register your models here.
from .models import Test, Question, Answer, Course, Module

admin.site.register(Test)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Course)
admin.site.register(Module)
