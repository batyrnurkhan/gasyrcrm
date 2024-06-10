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
    return range(1, value + 1)