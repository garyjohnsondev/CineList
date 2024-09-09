from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.core import mail
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.forms import PasswordChangeForm
from datetime import timedelta
import requests

from .forms import CreateAccountForm, SearchForm
from .models import Movie, User, Genre, FriendRequest, Email
from .forms import CreateAccountForm, SearchForm, BorrowRequestForm, MovieDetailsForm, EditProfileForm, UserPreferencesForm
from .models import Movie, User, Genre, FriendRequest, BorrowRequest
from .services import get_trending


def home(request):
    return render(request, "main/index/index.html")


def about(request):
    return render(request, 'main/index/about.html')


def api_index(request):
    return render(request, 'main/tmdb_api/api_index.html')


def api_fetch_results(request):
    keywords = request.GET["query"] #pull "keywords" param from get request
    if not keywords: #check if search was empty
        req = requests.get('https://api.themoviedb.org/3/discover/movie?api_key=0ba059be682204c1870cf30296aa5ddf&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1', params=request.GET)
    else:
        url = 'https://api.themoviedb.org/3/search/movie?api_key=0ba059be682204c1870cf30296aa5ddf&language=en-US&query=' + keywords + '&page=1&include_adult=false'
        req = requests.get(url, params=request.GET)
    results = req.json()["results"]
    if req.status_code == 200:#verify successful api call
        return render(request, 'main/tmdb_api/api_results.html', {'results': results})
    return HttpResponse('API Request Failure')

def create_account(request):
    if request.method == 'POST':
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            form.save()
            user_name = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user_name, password=raw_password)
            generic_subject = "Welcome to CineList"
            generic_message = "Welcome to CineList, " + user.first_name + "!\n"
            generic_message += "The first thing you should to is build out your CineList library with movies you own.\n"
            generic_message += "Once you have your library built, you should search for friends and begin sharing movies.\nThank you!"
            email = Email(
                subject=generic_subject,
                body=generic_message,
                from_email='noreply@cinelist.io',
                to=user.email,
                user_to=user
            )
            email.save()
            with mail.get_connection() as connection:
                mail.EmailMessage(
                    subject=email.subject,
                    body=email.body,
                    from_email=email.from_email,
                    to=[email.to],
                    connection=connection,
                ).send()
            login(request, user)
            return redirect('dashboard')
        else:
            form = CreateAccountForm()
            return render(request, 'registration/create_account.html', { 'form': form })
    else:
        form = CreateAccountForm()
    return render(request, 'registration/create_account.html', { 'form': form })


@login_required
def edit_profile(request):
    user = request.user
    if user.is_authenticated:
        if request.method == 'POST':
            form = EditProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                form = EditProfileForm(instance=request.user)
                alert = { 'type': 'alert-success', 'message': 'Your profile was succesfully updated!' }
                return render(request, 'registration/edit_profile.html', {'form': form, 'alert' : alert })
        else:
            form = EditProfileForm(instance=request.user)
            return render(request, 'registration/edit_profile.html', { 'form': form })
    else:
        return redirect("login")

@login_required
def change_password(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    else:
        if request.method == 'POST':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                alert = { 'type': 'alert-success', 'message': 'Your profile was succesfully updated!' }
                return redirect('edit_profile', alert)
        else:
            password_form = PasswordChangeForm(user=user)
            return render(request, 'accounts/change_password.html', {'password_form' : password_form})


@login_required
def dashboard(request):
    user = request.user
    if user.is_authenticated:
        context = {
            'library_count': Movie.objects.filter(user=user).count(),
            'sent_requests': BorrowRequest.objects.filter(sender=user, status=BorrowRequest.SENT),
            'received_requests' : BorrowRequest.objects.filter(receiver=user, status=BorrowRequest.SENT),
            'borrows': list_upcoming_borrows(request),
            'loans': list_upcoming_loans(request)
        }
        return render(request, "user/dashboard.html", context)
    else:
        return redirect("login")


@login_required
def profile(request):
    user = request.user
    if user.is_authenticated:
        context = {
            'sent_requests': BorrowRequest.objects.filter(sender=user, status=BorrowRequest.SENT),
            'received_requests' : BorrowRequest.objects.filter(receiver=user, status=BorrowRequest.SENT),
            'borrows': list_upcoming_borrows(request),
            'loans': list_upcoming_loans(request),
            'friends': request.user.friends_list.all()
        }
        return render(request, 'user/profile.html', context)
    else:
        return redirect("login")


@login_required
def view_profile(request, other_id):
    if request.user.is_authenticated:
        if other_id is request.user.id:
            return redirect('profile')
        else:
            user = request.user
            other_user = User.objects.get(id = other_id)

            friends = user.friends_list.all()
            if other_user in list(friends):
                return render(request, 'user/friend/profile.html', { 'user': user, 'other_user': other_user })
            else:
                try:
                    if FriendRequest.objects.filter(sender=other_user, receiver=user).exists():
                        return render(request, 'user/friend/accept_or_deny_request.html', { 'other_user': other_user })
                    else:
                        sentRequest = FriendRequest.objects.filter(sender=user, receiver=other_user).exists()
                        return render(request, 'user/friend/friend_request.html', { 'other_user': other_user, 'sentRequest': sentRequest })
                except ObjectDoesNotExist:
                    sentRequest = FriendRequest.objects.filter(sender=user, receiver=other_user).exists()
                    return render(request, 'user/friend/friend_request.html', { 'other_user': other_user, 'sentRequest': sentRequest })
    else:
        return redirect("login")


@login_required
def find_friend_index(request):
    user = request.user
    if user.is_authenticated:
        return render(request, 'main/find_friends_index.html')
    else:
        return redirect("login")


@login_required
def find_friend_results(request):
    this_user = request.user
    if this_user.is_authenticated:
        keywords = request.GET["keywords"]
        users = User.objects.filter(first_name__exact=keywords)
        return render(request, 'main/find_friends_results.html', { 'this_user': this_user, 'users': users })
    else:
        return redirect("login")


@login_required
def find_friend_results(request):
    user = request.user
    if user.is_authenticated:
        keywords = request.GET["keywords"]

        users = User.objects.annotate(
            search=SearchVector('username', 'first_name', 'last_name')
        ).filter(
            search=SearchQuery(keywords)
        )

        return render(request, 'main/find_friends_results.html',
            {
                'users': users
            })
    else:
        return redirect("login")


@login_required
def send_friend_request(request, other_id):
    if request.user.is_authenticated:
        other_user = User.objects.get(id = other_id)
        if other_user is not None:
            user = request.user
            friendRequest = FriendRequest(sender=user, receiver=other_user)  # sender sends a request to receiver
            friendRequest.save()

            generic_subject = "CineList friend request from " + user.first_name + ' ' + user.last_name
            generic_message = "Hello from CineList, \n" + user.first_name + ' ' + user.last_name + " would like to become your friend.\n"
            generic_message += "To reply to this friend request, please sign into your CineList account. Thank you!"

            email = Email(
                subject=generic_subject,
                body=generic_message,
                from_email='noreply@cinelist.io',
                to=other_user.email,
                user_to=other_user
            )
            email.save()
            with mail.get_connection() as connection:
                mail.EmailMessage(
                    subject=email.subject,
                    body=email.body,
                    from_email=email.from_email,
                    to=[email.to],
                    connection=connection,
                ).send()
            return view_profile(request, other_user.id)
        else:
            return render(request, 'main/find_friends_index.html', { 'open_requests' })
    else:
        return redirect("login")


@login_required
def cancel_friend_request(request, other_id):
    user = request.user
    if user.is_authenticated:
        other_user = User.objects.get(id=other_id)  # any user that is not request user
        if FriendRequest.objects.filter(sender=user, receiver=other_user).exists():     # If request user cancelled a request to a different user,
            friendRequest = FriendRequest.objects.get(sender=user, receiver=other_user) # delete the Friend Request
            friendRequest.delete()
        elif FriendRequest.objects.filter(sender=other_user, receiver=user).exists():   # If request user denies a request that was sent to them,
            friendRequest = FriendRequest.objects.get(sender=other_user, receiver=user) # delete the Friend Request
            friendRequest.delete()
        return view_profile(request, other_id=other_user.id)
    else:
        return redirect("login")


@login_required
def add_friend(request, other_id):
    user = request.user
    if user.is_authenticated:
        other_user = User.objects.get(id = other_id)
        user.friends_list.add(other_user)  # Add a different user to main user's friends list
        try:
            friendRequest = FriendRequest.objects.get(sender=other_user, receiver=user, status=FriendRequest.SENT)
            if friendRequest:
                friendRequest.delete()
        except ObjectDoesNotExist:
            pass

        return view_profile(request, other_id=other_id)
    else:
        return redirect("login")


@login_required
def remove_friend(request, other_id):
    user = request.user
    if user.is_authenticated:
        other_user = User.objects.get(id = other_id)
        user.friends_list.remove(other_user)    # Remove a different user from main user's friends list
        if FriendRequest.objects.filter(sender=user, receiver=other_user).exists():      # If request user cancelled a request to a different user,
            friendRequest = FriendRequest.objects.get(sender=user, receiver=other_user)  # delete the Friend Request
            friendRequest.delete()
        elif FriendRequest.objects.filter(sender=other_user, receiver=user).exists():    # If request user denies a request that was sent to them,
            friendRequest = FriendRequest.objects.get(sender=other_user, receiver=user)  # delete the Friend Request
            friendRequest.delete()
        return view_profile(request, other_id=other_user.id)
    else:
        return redirect("login")


@login_required
def list_friends(request):
    return render(request, 'user/friends.html', {'friends': request.user.friends_list.all()})


def findRating(request): #Searches through each country in tmdb api call to get the release date & rating json object for US
    for country in request:
        if country["iso_3166_1"] == "US":
            return country
    return None


@login_required
def add_movie(request, id): #Takes movie id as argument from request to add a movie to the current user's library
    if request.user.is_authenticated: #user is logged in
        if not request.method == 'POST':
            return redirect(request.META.HTTP_REFERER)
        else:
            url = "https://api.themoviedb.org/3/movie/" + id + "?api_key=0ba059be682204c1870cf30296aa5ddf&language=en-US&append_to_response=release_dates"
            req = requests.get(url).json() #get movie details

            #if 'status_code' in req:
                #TODO Error catching: redirect to page saying "movie does not exist"?
            movieSet = Movie.objects.filter(user=request.user, tmdbId=id)
            if movieSet:
                # messages.add_message(request, messages.ERROR, 'The movie you were trying to add is already in your library.')
                alert = {
                    'alert' : {
                        'type' : 'alert-danger',
                        'message' : 'The movie you were trying to add is already in your library.',
                }}
                return render(request, 'main/tmdb_api/api_index.html', alert)
            else:
                releaseRating = findRating((req["release_dates"])["results"])
                if releaseRating is None: #If movie was not released in US
                    currentRating = "N/A"
                else:
                    currentRating = ((releaseRating["release_dates"])[0])["certification"]

                movie_genres = [genre['name'] for genre in req['genres']]

                movie = Movie(user=request.user,
                              title = req["title"],
                              tmdbId = int(id),
                              releaseDate = req["release_date"],
                              searchableReleaseDate = req["release_date"],
                              runtime = timedelta(minutes=req["runtime"]) if req["runtime"] else None,
                              description = req["overview"] if req["overview"] else None,
                              imageLink = "http://image.tmdb.org/t/p/w185/" + req["poster_path"] if req["poster_path"] else None,
                              tmdbLink = "http://tmdb.org/movie/" + id,
                              budget = req["budget"] if req["budget"] else None,
                              revenue = req["revenue"] if req["revenue"] else None,
                              rating = currentRating,
                              genres = movie_genres,
                              format = request.POST.get('format')
                          )
                movie.save()

                alert = {
                    'alert' : {
                        'type' : 'alert-success',
                        'message' : 'Title added succesfully.',
                        'link' : 'library',
                        'link_message' : 'Go to your library.'
                }}

                return render(request, 'main/tmdb_api/api_index.html', alert)
    else: #user not logged in: return to login or home screen
        return redirect("login")


@login_required
def delete_movie(request, other_id, movie_id):
    user = request.user
    if user.is_authenticated:
        movies = list_movies(request, user)
        try:
            movie = Movie.objects.get(id=movie_id)
            if movie is not None:
                Movie.objects.filter(id=movie_id).delete()
                alert = { 'type': 'alert-success', 'message': 'Title was deleted successfully.' }
                return render(request, 'user/library.html', {'current_user' : user, 'other_user' : user, 'movies' : movies, 'alert' : alert, 'id' : user })
        except ObjectDoesNotExist as e:
            alert = { 'type': 'alert-danger', 'message': 'Could not delete title.'}
            return render(request, 'user/library.html', {'current_user' : user, 'other_user' : user, 'movies' : movies, 'alert' : alert, 'id' : user  })
    else:
        return redirect('login')


@login_required
def edit_movie(request, other_id, movie_id):
    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    elif not request.method == 'POST':
        redirect(request.META.get('HTTP_REFERER'))
    else:
        movies = list_movies(request, user)
        format = request.POST.get('format')
        try:
            movie = Movie.objects.get(id=movie_id)
            movie.format = format
            movie.save()
        except ObjectDoesNotExist:
            alert = { 'type': 'alert-danger', 'message': 'Could not update title (the object could not be found in our database).' }
            return render(request, 'user/library.html', { 'current_user' : user, 'other_user' : user, 'movies' : movies, 'alert' : alert, 'id' : user})
        return library(request, user.id)


@login_required
def library(request, other_id):
    current_user = request.user
    other_user = User.objects.get(id=other_id)
    if current_user.is_authenticated: #Verify user is logged in, otherwise redirect to homepage
        if other_user == current_user:
            movies = list_movies(request, user=current_user)
            return render(request, 'user/library.html', {'current_user' : current_user, 'movies' : movies, 'other_user' : other_user, 'id' : user })
        elif other_user in list(current_user.friends_list.all()):
            movies = list_movies(request, other_id)
            return render(request, 'user/friend/library.html', {'current_user' : current_user, 'movies' : movies, 'other_user' : other_user, 'id' : user })
        else: #User is not friends with target user
            alert = { 'type': 'alert-danger', 'message': 'You are not friends with this user.' }
            return render(request, 'user/dashboard.html', {'alert' : alert})
    else:
        return redirect("login")

@login_required
def list_movies(request, user):
    movies = None
    if user is not None:
        movies = Movie.objects.filter(user=user).order_by('id')
    return movies


@login_required
def set_user_preferences(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    else:
        if request.method == 'POST':
            print(user)
            form = UserPreferencesForm(request.POST, user=user)
            if form.is_valid():
                preferences = form.clean()
                form = UserPreferencesForm(user=user)
                alert = { 'type': 'alert-success', 'message': 'Your preferences were saved succesfully - even if it looks like they weren\'t' }
                return render(request, 'user/preferences.html', {'form': form, 'alert': alert})
            else:
                form = UserPreferencesForm(user=user)
                alert = { 'type': 'alert-warning', 'message': 'Something went wrong!' }
                return render(request, 'user/preferences.html', {'form': form, 'alert': alert})
        else:
            form = UserPreferencesForm(user=user)
            return render(request, 'user/preferences.html', {'form': form})


@login_required
def search(request):
    user = request.user
    if not user.is_authenticated: #Validate user
        return redirect("login")

    if request.method == 'POST':
        form = SearchForm(user, request.POST) #Pass user to form
        if form.is_valid():
            terms = form.getTerms()
            keywords = form.getKeywords()
            results = Movie.objects.filter(
                **terms
            )
            if keywords:
                results = results.annotate(
                    search = SearchVector('title', 'searchableReleaseDate') #Search for keywords in title, releaseDate
                ).filter(
                    search = keywords #Movies with specified keywords
                )
            if results:
                return render(request, 'main/search_results.html', {'form' : form, 'results': results})
            else:
                alert = { 'type': 'alert-danger', 'message': 'No movies were found.' }
                return render(request, 'main/search.html', {'form' : form , 'alert' : alert })
        else:
            return redirect(request.META.HTTP_REFERER)
    else:
        form = SearchForm(user, request.GET)
        return render(request, 'main/search.html', {'form': form})


@login_required
def browse(request):
    genres = Genre.objects.all()
    id_list = [friend.id for friend in request.user.friends_list.all()]
    results = Movie.objects.filter(
        user__in=id_list
    )
    parsedResults = {}
    for genre in genres:
        parsedResults[genre.name] = (results.filter(genres__contains=[genre.name])[::1])

    if results: #One or movies found
        return render(request, 'main/browse.html', { 'results': parsedResults, 'genres': genres, 'allmovies': results})
    else: #No movies found
        alert = { 'type': 'alert-danger', 'message': 'An error occurred.'}
        return render(request, 'main/browse.html', {'alert' : alert})


@login_required
def send_borrow_request(request, movie_id=None):
    if request.user.is_authenticated:
        user = request.user
        movie = Movie.objects.get(id=movie_id)
        form = BorrowRequestForm(movie=movie, active_user=user)

        if request.method == 'POST':
            form = BorrowRequestForm(movie, user, request.POST)
            if form.is_valid():
                start_date = form.clean_date()
                borrow_request = BorrowRequest(
                    movie = movie,
                    sender = user,
                    receiver = movie.user,
                    start_date = start_date,
                    borrow_duration = form.cleaned_data['borrow_duration'],
                    notes = form.cleaned_data['notes'],
                    status = BorrowRequest.SENT
                )
                borrow_request.save()

                recipient = movie.user.email

                generic_subject = "CineList borrow request from " + user.first_name + ' ' + user.last_name
                generic_message = "Hello from CineList! Your friend, " + user.first_name + ' ' + user.last_name + ", would like to borrow your movie, " + movie.title + '.\n'
                if form.cleaned_data['notes']:
                    generic_message += "Note from " + user.first_name + ": " + form.cleaned_data['notes'] + "\n"
                generic_message += "To reply to this borrow request, please sign into your CineList account. Thank you!"
                email = Email(
                    subject=generic_subject,
                    body=generic_message,
                    from_email='noreply@cinelist.io',
                    to=movie.user.email,
                    user_to=movie.user
                )
                email.save()
                with mail.get_connection() as connection:
                    mail.EmailMessage(
                        subject=email.subject,
                        body=email.body,
                        from_email=email.from_email,
                        to=[email.to],
                        connection=connection,
                    ).send()

                alert = { 'type': 'alert-success', 'message': 'Borrow request sent.' }
                return dashboard(request)
            else:
                return render(request, 'movie/send_borrow_request.html', { 'borrow_request_form': form, 'movie': movie, 'http_referer': request.META.get('HTTP_REFERER') })
        else:
            return render(request, 'movie/send_borrow_request.html', { 'borrow_request_form': form, 'movie': movie, 'http_referer': request.META.get('HTTP_REFERER') })
    else:
        return redirect('login')


@login_required
def update_borrow_request(request, borrow_request_id):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        borrow_request = BorrowRequest.objects.get(id=borrow_request_id)
        if borrow_request:
            status = request.GET.get('status')
            borrow_request.status = status
            borrow_request.save()
            alert = { 'type': 'alert-success', 'message': 'Borrow request successfully updated.' }
            return dashboard(request)
        else:
            alert = { 'type': 'alert-success', 'message': 'An error occured.' }
            return dashboard(request)


@login_required
def delete_borrow_request(request, borrow_request_id):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        borrow_request = BorrowRequest.objects.get(id=borrow_request_id)
        if borrow_request:
            all_requests = BorrowRequest.objects.all()
            all_requests.delete(id=borrow_request.id)
            alert = { 'type': 'alert-success', 'message': 'Borrow request successfully deleted.' }
            return dashboard(request)
        else:
            alert = { 'type': 'alert-success', 'message': 'An error occured.' }
            return dashboard(request)

@login_required
def list_upcoming_borrows(request):
    user = request.user
    borrows = BorrowRequest.objects.filter(sender=user, status=BorrowRequest.ACCEPTED).order_by('start_date')
    return borrows

@login_required
def list_upcoming_loans(request):
    user = request.user
    loans = BorrowRequest.objects.filter(receiver=user, status=BorrowRequest.ACCEPTED).order_by('start_date')
    return loans

@login_required
def messages(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        messages = Email.objects.filter(user_to=request.user).order_by('-date_sent')
        return render(request, 'user/messages.html', { 'email_messages' : messages })
