from django import template
from django.utils.html import format_html

register = template.Library()

@register.simple_tag
def render_grade_field(form, prefix, student_id):
    field_name = f"{prefix}{student_id}"
    return format_html("{} {}", form[field_name].label_tag(), form[field_name])
