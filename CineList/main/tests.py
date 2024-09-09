from django.test import TestCase, Client
from django.core.management import call_command
from django.urls import reverse
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from main.models import User, Movie, BorrowRequest, FriendRequest
from main.forms import BorrowRequestForm
import datetime

class AddMovieTestCase(TestCase):
    '''Tests TMDB API search and ability to add movies to a user's library
    using API data.'''

    def setUp(self):
        print("\033[0;32m Running add movie test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')
        response = self.client.get('/user/dashboard')
        self.user = response.context['user']

    def test_api_index_is_resolved(self):
        response = self.client.get('/api_index')
        self.assertEqual(response.resolver_match.func.__name__, 'api_index')

    def test_api_search_gets_results(self):
        response = self.client.get('/api_results', {'query': 'star wars', 'page': 1})
        self.assertEqual(response.resolver_match.func.__name__, 'api_fetch_results')
        self.assertIsNotNone(response.context['results'])
        self.assertEqual(response.context['results'][0].get('title'), 'Star Wars')
        return response.context['results'][0]

    def test_add_movie_is_successful(self):
        war_games = self.client.get('/api_results', {'query': 'wargames', 'page': 1})
        self.assertIsNotNone(war_games.context['results'])
        self.assertEqual(war_games.context['results'][0].get('title'), 'WarGames')
        tmdb_id = war_games.context['results'][0].get('id')
        response = self.client.post(reverse('add_movie', kwargs={'id': tmdb_id }), {'format': Movie.BLURAY})

        new_movie_was_added = Movie.objects.get(user=self.user, tmdbId=tmdb_id)
        self.assertIsNotNone(new_movie_was_added)
        self.assertEqual(new_movie_was_added.title, 'WarGames')
        self.assertEqual(new_movie_was_added.tmdbId, tmdb_id)
        self.assertEqual(new_movie_was_added.format, Movie.BLURAY)
        return war_games

    def test_movie_already_exists(self):
        star_wars = self.test_api_search_gets_results()
        existing_movie = Movie.objects.get(user=self.user, tmdbId=star_wars.get('id'))
        response = self.client.post(reverse('add_movie', kwargs={'id': star_wars.get('id') }), {'format': Movie.DVD})
        was_new_movie_added = Movie.objects.filter(user=self.user, tmdbId=star_wars.get('id'))
        self.assertEqual(was_new_movie_added.count(), 1)
        was_new_movie_added = was_new_movie_added[0]
        self.assertEqual(was_new_movie_added.id, existing_movie.id)

    def test_add_movie_is_unsuccessful_incomplete_data(self):
        response = self.client.get('/api_results', {'query': 'The Harry Potter Saga Analyzed', 'page': 1})
        self.assertEqual(response.context['results'][0].get('title'), 'The Harry Potter Saga Analyzed')
        tmdb_id = response.context['results'][0].get('id')
        with self.assertRaises((IntegrityError, ValidationError)):
            self.client.post(reverse('add_movie', kwargs={'id': tmdb_id }), {'format': Movie.DVD})

class DeleteMovieTestCase(TestCase):
    '''Tests deletion of a movie from a user's library.'''

    def setUp(self):
        print("\033[0;32m Running delete movie test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')

        response = self.client.get('/user/library')
        self.assertEqual(response.resolver_match.func.__name__, 'library')
        self.user = response.context['user']

    def test_delete_movie_is_successful(self):
        response = self.client.get('/user/library')
        user_movies = response.context['movies']
        movie_to_delete = user_movies[0]
        deleted_response = self.client.post(reverse('delete_movie', kwargs={'movie_id': movie_to_delete.id}))
        self.assertNotIn(movie_to_delete, deleted_response.context['movies'])
        return movie_to_delete

    def test_delete_movie_unsuccessful_not_in_library(self):
        movie_to_delete = self.test_delete_movie_is_successful()
        existing_movies = Movie.objects.filter(user=self.user)
        self.assertNotIn(movie_to_delete, existing_movies)
        deleted_response = self.client.post(reverse('delete_movie', kwargs={'movie_id': movie_to_delete.id}))
        self.assertNotIn(movie_to_delete, deleted_response.context['movies'])

class SearchTestCase(TestCase):
    '''Tests search functionality'''

    def setUp(self):
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')

        response = self.client.get('/search')
        self.assertEqual(response.resolver_match.func.__name__, 'search')

    def test_get_request(self):
        response = self.client.post('/search')

        try:
            results = response.context['results']
        except KeyError:
            pass

    def test_no_results(self):
        response = self.client.post('/search', {'keywords': 'syzygy'})

        try:
            results = response.context['results']
        except KeyError:
            pass

    def test_no_arguments(self):
        response = self.client.post('/search')
        results = response.context['results']

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 29) #Expect 29 movies

    def test_specific_keywords(self):
        response = self.client.post('/search', {'keywords': 'story'})
        results = response.context['results']

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 3) #Expect the Toy Story trilogy

    def test_specific_user(self):
        response = self.client.post('/search', {'user': 2})
        results = response.context['results']

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 11) #Expect 11 movies of Richard Clark

    def test_specific_genre(self):
        response = self.client.post('/search', {'genre': 'Drama'})
        results = response.context['results']

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 3) #Expect 3 movies labeled "drama"

    def test_specific_format(self):
        response = self.client.post('/search', {'format': 'K'})
        results = response.context['results']

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2) #Expect 2 movies labeled 4k

class BrowseTestCase(TestCase):
    '''Tests browse functionality'''

    def setUp(self):
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')

        response = self.client.get('/browse')
        self.assertEqual(response.resolver_match.func.__name__, 'browse')

    def test_no_results(self):
        response = self.client.post('/browse')
        self.client.logout()
        self.client.login(username='demo_nofriends', password='nofriends')

        try:
            results = response.context['results']
        except KeyError:
            pass

    def test_expected_movies(self):
        response = self.client.post('/browse')
        results = response.context['allmovies']

        self.assertEqual(len(results), 29) #Expect 29 movies

    def test_expected_genres(self):
        response = self.client.post('/browse')
        parsedResults = response.context['results']
        genres = response.context['genres']

        self.assertEqual(len(parsedResults), 19) #Expect 19 genres
        self.assertEqual(len(genres), 19) #Expect 19 genres

class SendBorrowRequestTestCase(TestCase):
    """Tests ability to send borrow requests."""

    def setUp(self):
        print("\033[0;32m Running send borrow request test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='brandongeorge', password='golden134')
        response = self.client.get('/user/dashboard')
        self.user = response.context['user']

    def get_movie_to_borrow(self):
        count = 0
        all_friends = self.user.friends_list.all()
        send_to = all_friends[count]
        self.assertIsNotNone(send_to)

        movie_set = Movie.objects.filter(user=send_to)
        while not movie_set:
            count += 1
            send_to = all_friends[count]
            movie_set = Movie.objects.filter(user=send_to)

        return movie_set[0]

    def test_send_borrow_request_is_successful(self):
        borrow_requests_count = BorrowRequest.objects.count()
        movie_to_borrow = self.get_movie_to_borrow()
        data = {
            'start_date' : datetime.date.today() + datetime.timedelta(days=1),
            'borrow_duration' : 3,
            'notes' : 'Test valid borrow request.'
        }
        form = BorrowRequestForm(movie=movie_to_borrow, active_user=self.user, data=data)
        self.assertTrue(form.is_valid())

        response = self.client.post(reverse('send_borrow_request', kwargs={'movie_id': movie_to_borrow.id}), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BorrowRequest.objects.count(), borrow_requests_count + 1)

    def test_send_borrow_request_fails_start_date_before_now(self):
        borrow_requests_count = BorrowRequest.objects.count()
        movie_to_borrow = self.get_movie_to_borrow()
        data = {
            'start_date' : datetime.date.today() - datetime.timedelta(days=1), # invalid
            'borrow_duration' : 3,
            'notes' : 'Test invalid borrow request - start date before current day.'
        }

        form = BorrowRequestForm(movie=movie_to_borrow, active_user=self.user, data=data)
        self.assertFalse(form.is_valid())

        response = self.client.post(reverse('send_borrow_request', kwargs={'movie_id': movie_to_borrow.id}), data)
        self.assertEqual(BorrowRequest.objects.count(), borrow_requests_count)

    def test_send_borrow_request_fails_invalid_borrow_duration_1(self):
        borrow_requests_count = BorrowRequest.objects.count()
        movie_to_borrow = self.get_movie_to_borrow()
        data = {
            'start_date' : datetime.date.today() + datetime.timedelta(days=1),
            'borrow_duration' : 0, # invalid
            'notes' : 'Test invalid borrow request - borrow duration 0 days not a choice.'
        }
        form = BorrowRequestForm(movie=movie_to_borrow, active_user=self.user, data=data)
        self.assertFalse(form.is_valid())

        response = self.client.post(reverse('send_borrow_request', kwargs={'movie_id': movie_to_borrow.id}), data)
        self.assertEqual(BorrowRequest.objects.count(), borrow_requests_count)


    def test_send_borrow_request_fails_invalid_borrow_duration_2(self):
        borrow_requests_count = BorrowRequest.objects.count()
        movie_to_borrow = self.get_movie_to_borrow()
        data = {
            'start_date' : datetime.date.today() + datetime.timedelta(days=1),
            'borrow_duration' : 15, # invalid
            'notes' : 'Test invalid borrow request - borrow duration 15 days not a choice.'
        }

        form = BorrowRequestForm(movie=movie_to_borrow, active_user=self.user, data=data)
        self.assertFalse(form.is_valid())

        response = self.client.post(reverse('send_borrow_request', kwargs={'movie_id': movie_to_borrow.id}), data)
        self.assertEqual(BorrowRequest.objects.count(), borrow_requests_count)

    def test_send_borrow_request_fails_movie_deleted_before_form_submit(self):
        borrow_requests_count = BorrowRequest.objects.count()
        movie_to_borrow = self.get_movie_to_borrow()


        deleted_response = self.client.post(reverse('delete_movie', kwargs={'movie_id': movie_to_borrow.id}))
        self.assertEqual(deleted_response.status_code, 200)

        with self.assertRaises(Movie.DoesNotExist):
            response = self.client.post(reverse('send_borrow_request', kwargs={'movie_id': movie_to_borrow.id}), {
                    'start_date' : datetime.date.today() + datetime.timedelta(days=1),
                    'borrow_duration' : 3,
                    'notes' : 'Test invalid borrow request - movie deleted before form submit.'
                })
            self.assertEqual(response.status_code, 404)
            self.assertEqual(BorrowRequest.objects.count(), borrow_requests_count)


class AcceptDenyCancelBorrowRequestTestCase(TestCase):
    """Tests ability to accept/deny/cancel a sent or received borrow request."""

    def setUp(self):
        print("\033[0;32m Running accept/deny/cancel borrow request test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')
        response = self.client.get('/user/dashboard')
        self.user = response.context['user']

    def create_borrow_request(self, movie, sender):
        borrow_request = BorrowRequest(
            movie = movie,
            sender = sender,
            receiver = movie.user,
            start_date = datetime.date.today() + datetime.timedelta(days=1),
            borrow_duration = 3,
            notes = "Test borrow request.",
            status = BorrowRequest.SENT
        )
        borrow_request.save()
        return borrow_request

    def get_movie_to_borrow(self):
        count = 0
        all_friends = self.user.friends_list.all()
        send_to = all_friends[count]
        self.assertIsNotNone(send_to)

        movie_set = Movie.objects.filter(user=send_to)
        while not movie_set:
            count += 1
            send_to = all_friends[count]
            movie_set = Movie.objects.filter(user=send_to)

        return movie_set[0]

    def test_cancel_borrow_request_successful(self):
        movie = self.get_movie_to_borrow()
        borrow_request = self.create_borrow_request(movie, self.user)

        response = self.client.get(reverse('update_borrow_request', kwargs={'borrow_request_id': borrow_request.id}), {'status': BorrowRequest.CANCELLED})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BorrowRequest.objects.get(id=borrow_request.id).status, BorrowRequest.CANCELLED)

    def test_accept_borrow_request_successful(self):
        movie = self.get_movie_to_borrow()
        borrow_request = self.create_borrow_request(movie, self.user)

        response = self.client.get(reverse('update_borrow_request', kwargs={'borrow_request_id': borrow_request.id}), {'status': BorrowRequest.ACCEPTED})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BorrowRequest.objects.get(id=borrow_request.id).status, BorrowRequest.ACCEPTED)

    def test_deny_borrow_request_successful(self):
        movie = self.get_movie_to_borrow()
        borrow_request = self.create_borrow_request(movie, self.user)

        response = self.client.get(reverse('update_borrow_request', kwargs={'borrow_request_id': borrow_request.id}), {'status': BorrowRequest.DENIED})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BorrowRequest.objects.get(id=borrow_request.id).status, BorrowRequest.DENIED)


class AddFriendTestCase(TestCase):
    """"Tests Find Friends Search and adding friends to a friends list"""

    def setUp(self):
        print("\033[0;32m Running add friend test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')
        response = self.client.get('/user/dashboard')
        self.user = response.context['user']

    def test_find_friends_index_is_resolved(self):
        response = self.client.get(reverse('find_friend_index'))
        self.assertEqual(response.resolver_match.func.__name__, 'find_friend_index')

    def test_find_friends_gets_results(self):
        response = self.client.get(reverse('find_friend_results'), {'keywords': 'Richard'})
        self.assertIsNotNone(response.context.get('users'))
        self.assertEqual(response.context.get('users')[0].first_name, 'Richard')
        return response.context.get('users')[0]

    def test_add_friend_is_successful(self):
        added_friend = User.objects.get(id=7)
        new_friend_request = FriendRequest(sender=self.user, receiver=added_friend, status=FriendRequest.SENT)
        new_friend_request.save()
        response = self.client.post(reverse('request_accepted', kwargs={'other_id': 7}))
        self.assertIn(added_friend, self.user.friends_list.all())
        return added_friend

class RemoveFriendTestCase(TestCase):
    """Tests removal of a user from a friends list"""

    def setUp(self):
        print("\033[0;32m Running remove friend test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')
        response = self.client.get('/user/dashboard')
        self.user = response.context['user']

    def test_remove_friend_is_successful(self):
        response = self.client.get('/user/profile')
        existing_friends = self.user.friends_list.all()
        self.assertIsNotNone(existing_friends)
        friend_to_remove = existing_friends[0]
        deleted_response = self.client.post(reverse('remove_friend', kwargs={'other_id': friend_to_remove.id}))
        self.assertNotIn(friend_to_remove, existing_friends)
        return friend_to_remove

    def test_remove_friend_unsuccessful_not_in_list(self):
        friend_to_remove = self.test_remove_friend_is_successful()
        existing_friends = self.user.friends_list.all()
        self.assertNotIn(friend_to_remove, existing_friends)
        deleted_response = self.client.post(reverse('remove_friend', kwargs={'other_id': friend_to_remove.id}))
        self.assertNotIn(friend_to_remove, existing_friends)


class SendFriendRequestTestCase(TestCase):
    """Tests ability to send friend requests."""

    def setUp(self):
        print("\033[0;32m Running send friend request test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='brandongeorge', password='golden134')
        response = self.client.get('/user/dashboard')
        self.user = response.context['user']

    def get_user_to_befriend(self):
        all_users = User.objects.all()
        return all_users[0]

    def test_send_friend_request_is_successful(self):
        friend_requests_count = FriendRequest.objects.count()
        user_to_befriend = self.get_user_to_befriend()

        response = self.client.post(reverse('request_sent', kwargs={'other_id': user_to_befriend.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FriendRequest.objects.count(), friend_requests_count + 1)


class CancelDenyFriendRequestTestCase(TestCase):
    """Tests ability to cancel/deny a sent or received Friend Request"""

    def setUp(self):
        print("\033[0;32m Running cancel/deny friend request test cases... \033[0m")
        self.client = Client()
        call_command('loaddata', 'test_data.json')
        self.client.login(username='demo_superuser', password='superuser')
        response = self.client.get('/user/dashboard')
        self.user = response.context['user']

    def create_friend_request(self, sender, receiver):
        friend_request = FriendRequest(
            sender = sender,
            receiver = receiver,
            status = FriendRequest.SENT
        )
        friend_request.save()
        return friend_request

    def test_cancel_friend_request_successful(self):
        receiver = User.objects.get(pk=3)
        friend_request = self.create_friend_request(self.user, receiver)
        friend_request_count = FriendRequest.objects.count()

        response = self.client.get(reverse('request_cancelled', kwargs={'other_id': receiver.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FriendRequest.objects.count(), friend_request_count - 1)

    def test_deny_friend_request_successful(self):
        sender = User.objects.get(pk=4)
        friend_request = self.create_friend_request(sender, self.user)
        friend_request_count = FriendRequest.objects.count()

        response = self.client.get(reverse('request_cancelled', kwargs={'other_id': sender.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FriendRequest.objects.count(), friend_request_count - 1)
