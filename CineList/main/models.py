from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres import fields
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
from datetime import timedelta, date


class User(AbstractUser):
    first_name = models.CharField(max_length = 30, blank = False)
    last_name = models.CharField(max_length = 30, blank = False)
    email = models.EmailField(max_length = 254, blank = False)
    phone_number = models.CharField(max_length = 10, blank = True)
    address = models.CharField(max_length = 100, blank = True)
    friends_list = models.ManyToManyField("self")

    # class Meta:
    #     permissions = ((),)

    def getFullName(self):
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return self.getFullName()

class Movie(models.Model):
    IN_LIBRARY = 1
    BORROWED = 2
    OVERDUE = 3
    STATUS_CHOICES = (
        (IN_LIBRARY, 'In library'),
        (BORROWED, 'Borrowed'),
        (OVERDUE, 'Overdue')
    )
    VHS = 'V'
    DVD = 'D'
    BLURAY = 'B'
    _4K = 'K'
    FORMAT_CHOICES = (
        (None, ''),       # for use in search, will not validate if persisted
        (VHS, 'VHS Tape'),
        (DVD, 'DVD'),
        (BLURAY, 'Blu-ray'),
        (_4K, '4K UHD')
    )

    def defaultConditions():
        return dict(conditions=[])

    def defaultPreferences():
        return dict(data=dict(borrow_duration='2 weeks'))

    user = models.ForeignKey('User', on_delete=models.CASCADE, blank=False)
    title = models.CharField(max_length = 128)
    tmdbId = models.IntegerField()
    releaseDate = models.DateField()
    searchableReleaseDate = models.CharField(max_length = 10)
    runtime = models.DurationField(blank=True)
    description = models.CharField(max_length = 8192, blank=True)
    imageLink = models.CharField(max_length = 64, blank=True)
    tmdbLink = models.CharField(max_length = 64, blank=True)
    budget = models.IntegerField(blank=True)
    revenue = models.IntegerField(blank=True)
    rating = models.CharField(max_length = 8, blank=True)
    genres = fields.ArrayField(models.CharField(max_length=250, blank=True), blank=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=IN_LIBRARY)
    format = models.CharField(max_length=2, choices=FORMAT_CHOICES, default=DVD, blank=False)
    condition = fields.JSONField(encoder=DjangoJSONEncoder, default=defaultConditions)
    preferences = fields.JSONField(encoder=DjangoJSONEncoder, default=defaultPreferences)

    def __str__(self):
        return self.title

class Genre(models.Model):
    tmdb_id = models.IntegerField()
    name = models.CharField(max_length=250, blank=False)

    def __str__(self):
        return self.name


class FriendRequest(models.Model):
    SENT = 'S'
    ACCEPTED = 'A'
    CANCELLED = 'C'

    STATUS_CHOICES = (
        (SENT, 'Sent'),
        (ACCEPTED, 'Accepted'),
        (CANCELLED, 'Cancelled')
    )

    sender = models.ForeignKey('User', related_name="friend_request_sender", on_delete=models.CASCADE, blank=False)
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, blank=False)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=SENT)


class BorrowRequest(models.Model):
    def validate_date(date):
        if date < date.today():
            raise ValidationError("Date cannot be in the past",  code='invalid')

    SENT = 'S'
    ACCEPTED = 'A'
    DENIED = 'D'
    CANCELLED = 'C'

    STATUS_CHOICES = (
        (SENT, 'Sent'),
        (ACCEPTED, 'Accepted'),
        (DENIED, 'Denied'),
        (CANCELLED, 'Cancelled')
    )

    BORROW_DURATION_CHOICES = (
        (1, '1 day'),
        (2, '2 days'),
        (3, '3 days'),
        (4, '4 days'),
        (5, '5 days'),
        (6, '6 days'),
        (7, '1 week'),
        (8, '8 days'),
        (9, '9 days'),
        (10, '10 days'),
        (11, '11 days'),
        (12, '12 days'),
        (13, '13 days'),
        (14, '2 weeks'),
    )

    movie = models.ForeignKey('Movie', on_delete=models.CASCADE, blank=False)
    sender = models.ForeignKey('User', related_name="borrow_request_sender", on_delete=models.CASCADE, blank=False)
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, blank=False)
    start_date = models.DateField(blank=False, validators=[validate_date])
    borrow_duration = models.IntegerField(blank=False, choices=BORROW_DURATION_CHOICES, default=3)
    notes = models.CharField(blank=True, max_length=500)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=SENT)

class Email(models.Model):
    date_sent = models.DateTimeField(blank=False, auto_now_add=True)
    subject = models.CharField(blank=True, max_length=500)
    body = models.CharField(blank=False, max_length=36000)
    from_email = models.EmailField(blank=False)
    to = models.EmailField(blank=False)
    user_to = models.ForeignKey('User', related_name='message_user_to', on_delete=models.CASCADE, blank=False)

class UserPreferences(models.Model):
    EXCHANGE_TYPE_CHOICES = (
        ('PICK_UP', 'Pick up'),
        ('DROP_OFF', 'Drop off')
    )

    EXCHANGE_LOCATION_CHOICES = (
        ('DEFAULT', 'My address'),
        ('OTHER', 'Other')
    )

    user = models.ForeignKey('User', on_delete=models.CASCADE, blank=False)
    show_personal_info = models.BooleanField(default=True)
    start_loan_exchange_type = models.CharField(max_length=12, choices=EXCHANGE_TYPE_CHOICES, default='PICK_UP')
    end_loan_exchange_type = models.CharField(max_length=12, choices=EXCHANGE_TYPE_CHOICES, default='DROP_OFF')
    exchange_location_choice = models.CharField(max_length=12, choices=EXCHANGE_LOCATION_CHOICES, default='DEFAULT')
    exchange_location = models.CharField(max_length=100, blank=True)
    favorite_genre = models.ForeignKey('Genre', on_delete=models.CASCADE, blank=True)
