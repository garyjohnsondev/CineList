from django.template import Library
from datetime import datetime,timedelta

register = Library()

@register.filter(expects_localtime=True)
def parse_date(value):
    if value is not '':
        return datetime.strptime(value, "%Y-%m-%d")
    else:
        return ''

@register.filter(name="get_due_date")
def get_due_date(start, duration):
    return start + timedelta(days=duration)
