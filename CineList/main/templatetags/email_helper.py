from django.template import Library

register = Library()

@register.filter(name='br_replace')
def br_replace(string):
    newstr = string.replace('\n', '<br/>')
    return newstr
