from django import template
from django.contrib.contenttypes.models import ContentType

from courses.models import Test, Lesson

register = template.Library()


@register.filter
def is_user_enrolled(course, user):
    return course.users.filter(id=user.id).exists()


@register.filter
def format_phone_number(number):
    return f"+{number[0:1]} ({number[1:4]}) {number[4:7]} {number[7:9]} {number[9:11]}"


@register.filter
def get_lesson_submission(queryset, object_id):
    test = Test.objects.filter(object_id=object_id, content_type=ContentType.objects.get_for_model(Lesson))[0]
    submissions = queryset.filter(test=test)
    if len(submissions) > 0:
        return submissions[0]
    return False


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)
