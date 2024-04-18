from django import template
register = template.Library()

@register.filter
def is_user_enrolled(course, user):
    return course.users.filter(id=user.id).exists()

@register.filter
def format_phone_number(number):
    return f"{number[0:2]} ({number[2:5]}) {number[5:8]} {number[8:10]} {number[10:12]}"
