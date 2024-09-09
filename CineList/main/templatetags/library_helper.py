from django.template import Library
from main.models import Movie

register = Library()

@register.filter(name='status_formatter')
def status_formatter(status):
#     html = "<span class=\"badge badge-pill"
#     if status is 2:
#         html += 'badge-danger'
#     elif status is 1:
#         html += 'badge-warning'
#     else:
#         html += 'badge-success'
#     html+= '">'
    html = ''
    if status is 3:
        html += 'Overdue'
    elif status is 2:
        html += 'Borrowed'
    else:
        html += 'In library'
    # html += "</span>"
    return html

@register.filter(name='media_formatter')
def media_formatter(type):
    if type is 'V':
        return 'VHS Tape'
    elif type is 'K':
        return '4k UHD'
    elif type is 'B':
        return 'Blu-ray'
    else:
        return 'DVD'

@register.filter(name='availabilty_formatter')
def availabilty_formatter(borrow_status):
    # html = "<span class=\"badge badge-pill"

    if borrow_status is Movie.OVERDUE:
        # html += "badge-success\"> Available"
        return "On loan - overdue"
    elif borrow_status is Movie.BORROWED:
        # html += "badge-warning\">
        return "On loan"
    else:
        return "Available"

        # html += "badge-warning\">
    # html += "</span>"

    # return html
