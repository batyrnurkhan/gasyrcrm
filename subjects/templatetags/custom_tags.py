import os

from django import template

from subjects.models import TaskSubmission

register = template.Library()


@register.filter
def is_user_enrolled(course, user):
    return course.users.filter(id=user.id).exists()


@register.filter
def format_phone_number(number):
    return f"+{number[0:1]} ({number[1:4]}) {number[4:7]} {number[7:9]} {number[9:11]}"


@register.filter
def divide(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def key(d, k):
    return d[k]


@register.filter
def filename(value):
    return os.path.basename(value.file.name)


@register.filter
def submission_filename(value, user):
    submission = value.submissions.filter(student=user).first()
    print(submission)
    if submission:
        return os.path.basename(submission.file.name)
    return ""

@register.filter
def get_task_submission(task, user):
    return TaskSubmission.objects.filter(task=task, student=user).first()