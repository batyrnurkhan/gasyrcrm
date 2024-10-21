from django import template
from django.contrib.contenttypes.models import ContentType
from courses.models import Test, Lesson, TestSubmission

register = template.Library()

@register.filter
def is_user_enrolled(course, user):
    return course.users.filter(id=user.id).exists()


@register.filter
def get_lesson_submission(submissions, lesson):
    tests = Test.objects.filter(object_id=lesson.id, content_type=ContentType.objects.get_for_model(Lesson))
    print(f"Checking tests for lesson ID {lesson.id} ({lesson.lesson_name}) in module {lesson.module.module_name}")
    print(f"Tests found for lesson {lesson.lesson_name}: {tests}")

    if tests.exists():
        submission = submissions.filter(test__in=tests).first()
        print(f"Submission found for lesson {lesson.lesson_name}: {submission}")
        return submission
    print(f"No submission found for lesson {lesson.lesson_name}")
    return None

@register.filter
def get_homework_submission(homework_submissions, lesson):
    # Достаем все домашние работы для данного урока по объекту lesson
    homework = homework_submissions.filter(lesson=lesson).first()
    print(f"Lesson ID: {lesson.id}, Homework found: {homework}")
    return homework

@register.filter
def format_phone_number(number):
    return f"+{number[0:1]} ({number[1:4]}) {number[4:7]} {number[7:9]} {number[9:11]}"

@register.filter
def addstr(arg1, arg2):
    return str(arg1) + str(arg2)

@register.filter
def calculate_completion_percentage(course, user):
    return course.calculate_completion_percentage(user)

@register.filter
def get_pass(phone, request):
    return request.session.get(phone, 'Expired')

@register.filter
def get_module_submission(submissions, module):
    tests = Test.objects.filter(object_id=module.id, content_type=ContentType.objects.get_for_model(module.__class__))
    print(f"Tests found for module {module.module_name}: {tests}")
    return submissions.filter(test__in=tests).first()