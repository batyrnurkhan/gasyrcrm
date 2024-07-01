import datetime

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def add_days(value, days):
    if isinstance(value, datetime.date):
        return value + datetime.timedelta(days=days)
    return value

@register.filter
def get_range(value):
    if value is None:
        value = 0  # Default to 0 if the value is None
    return range(1, value + 1)

@register.filter
def range_filter(value):
    return range(value)

@register.filter
def subtract(value, arg):
    return value - arg