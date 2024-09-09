from django.template import Library
from main.models import FriendRequest

register = Library()

@register.filter(name='count_open_requests')
def count_open_requests(user):
    open_requests = FriendRequest.objects.filter(receiver=user, status=FriendRequest.SENT)
    if open_requests:
        return open_requests.count()
    else:
        return

@register.filter(name='get_open_requests')
def get_open_requests(user):
    open_requests = FriendRequest.objects.filter(receiver=user, status=FriendRequest.SENT)
    if open_requests:
        return open_requests
    else:
        return

@register.filter(name='get_open_sent_requests')
def get_open_sent_requests(user):
    open_requests = FriendRequest.objects.filter(sender=user, status=FriendRequest.SENT)
    if open_requests:
        return open_requests
    else:
        return
