from django import template
register = template.Library()

@register.filter
def is_user_enrolled(course, user):
    return course.users.filter(id=user.id).exists()
