from django import template
register = template.Library()


@register.filter
def is_user_enrolled(course, user):
    return course.users.filter(id=user.id).exists()


@register.filter
def format_phone_number(number):
    return f"+{number[0:1]} ({number[1:4]}) {number[4:7]} {number[7:9]} {number[9:11]}"

