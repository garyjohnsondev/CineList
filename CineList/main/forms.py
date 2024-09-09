from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model, authenticate
import datetime
from main.models import Genre, Movie, User, BorrowRequest, UserPreferences


class CreateAccountForm(UserCreationForm):
    class Meta:
        model = get_user_model() #User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'username', 'password1', 'password2')

    first_name = forms.CharField(
        max_length = 30,
        required = True,
        help_text = 'Please enter your first name.'
    )
    last_name = forms.CharField(
        max_length = 30,
        required = True,
        help_text =
        'Please enter your last name.'
    )
    email = forms.EmailField(
        max_length = 254,
        help_text = 'Please enter your email address.'
    )
    phone_number = forms.CharField(
        max_length = 10,
        help_text = 'Optional. Please enter your phone number.',
        required = False
    )


class EditProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'address'
        )

class SearchForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        self.user_queryset = user.friends_list.all()
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['user'] = forms.ModelChoiceField(
            queryset = self.user_queryset,
            required = False,
            empty_label = ''
        )

    def getTerms(self):
        terms = self.cleaned_data

        if terms.get('user') is None:
            id_list = [friend.id for friend in self.user_queryset] #Get all friends in friends_list
        else:
            id_list = [terms.get('user')]

        filters = dict(user__in=id_list)

        if terms.get('genre'):
            filters['genres__contains'] = [terms.get('genre').name]

        if terms.get('format'):
            filters['format'] = terms.get('format')

        return filters

    def getKeywords(self):
        terms = self.cleaned_data
        return terms.get('keywords')

    class Meta:
        model = 'Movie'
        fields = ('keywords', 'user', 'genres', 'format',)  #TODO: implement distance w/google api,

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

    keywords = forms.CharField(
        label = "Search",
        max_length = 250,
        required = False,
    )
    user = forms.ModelChoiceField(
        queryset = None,
        required = False,
        empty_label = ''
    )
    genre = forms.ModelChoiceField(
        label = "Genre",
        queryset = Genre.objects.all(),
        to_field_name = 'name',
        required = False,
        empty_label = ''
    )
    format = forms.ChoiceField(
        choices = Movie.FORMAT_CHOICES,
        required = False,
    )
    # borrow_duration = forms.ChoiceField(
    # 	choices = blank_choice + BORROW_DURATION_CHOICES,
    # 	required = False,
    # )


class BorrowRequestForm(ModelForm):
    def __init__(self, movie, active_user, *args, **kwargs):
        self.movie = movie
        self.active_user = active_user
        super(BorrowRequestForm, self).__init__(*args, **kwargs)

    class Meta:
        model = BorrowRequest
        fields = ['start_date', 'borrow_duration', 'notes']

    start_date = forms.DateField(
        widget=forms.DateInput(
                format='%m/%d/%Y',
                attrs={'class': 'form-control', 'id': '#datetimepicker1', 'data-provide': 'datepicker'}
            ),
        input_formats=('%m/%d/%Y', '%Y-%m-%d'),
        required=True,
        # validators=[validate_date]
    )
    borrow_duration = forms.ChoiceField(
        choices = BorrowRequest.BORROW_DURATION_CHOICES,
        required = True
    )
    notes = forms.CharField(
        widget=forms.Textarea(),
        required = False
    )

    def clean_date(self):
        date = self.cleaned_data['start_date']
        if date < datetime.date.today():
            raise forms.ValidationError(_("Date cannot be in the past"),  code='invalid')
        return date


class MovieDetailsForm(forms.Form):
    VHS = 'V'
    DVD = 'D'
    BLURAY = 'B'
    _4K = 'K'
    FORMAT_CHOICES = (
        (VHS, 'VHS Tape'),
        (DVD, 'DVD'),
        (BLURAY, 'Blu-ray'),
        (_4K, '4K UHD')
    )

    format = forms.ChoiceField(
        label = "Format",
        choices = FORMAT_CHOICES,
        required = True
    )


class UserPreferencesForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UserPreferencesForm, self).__init__(*args, **kwargs)

    class Meta:
        model = UserPreferences
        fields = ('show_personal_info', 'start_loan_exchange_type', 'end_loan_exchange_type', 'exchange_location_choice',
            'exchange_location', 'favorite_genre')

        def clean(self):
            show_personal_info = self.cleaned_data['show_personal_info']
            start_loan_exchange_type = self.cleaned_data['start_loan_exchange_type']
            end_loan_exchange_type = self.cleaned_data['end_loan_exchange_type']
            exchange_location_choice = self.cleaned_data['exchange_location_choice']
            exchange_location = self.cleaned_data['exchange_location']
            preferences = None

            try:
                preferences = UserPreferences.get(user=self.user)
                preferences.show_personal_info = show_personal_info if show_personal_info else preferences.show_personal_info
                preferences.start_loan_exchange_type = start_loan_exchange_type if start_loan_exchange_type else preferences.start_loan_exchange_type
                preferences.end_loan_exchange_type = end_loan_exchange_type if end_loan_exchange_type else preferences.end_loan_exchange_type
                preferences.exchange_location_choice = exchange_location_choice if exchange_location_choice else preferences.exchange_location_choice
                preferences.exchange_location = exchange_location
                preferences.favorite_genre = favorite_genre
            except:
                preferences = UserPreferences(
                    user=self.user,
                    show_personal_info=show_personal_info,
                    start_loan_exchange_type=start_loan_exchange_type,
                    end_loan_exchange_type=end_loan_exchange_type,
                    exchange_location_choice=exchange_location_choice,
                    exchange_location=exchange_location,
                    favorite_genre=favorite_genre
                )

            preferences.save()
            return preferences
