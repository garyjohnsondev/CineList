from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.contrib.auth import login as auth_login, logout as auth_logout
from . import views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', views.home, name = 'index'),
    path('about', views.about, name='about'),
    path('home', views.home, name='home'),
    path('api_index', views.api_index, name='api_index'),
    path('api_results', views.api_fetch_results, name='api_results'),
    path('user/dashboard', views.dashboard, name='dashboard'),
    path('user/profile', views.profile, name = 'profile'),
    path('user/profile/edit', views.edit_profile, name = 'edit_profile'),
    path('user/library/add_movie&<str:id>', views.add_movie, name='add_movie'),
    path('user/<int:other_id>/library', views.library, name='library'),
    path('user/<int:other_id>/library/delete_movie&<str:movie_id>', views.delete_movie, name='delete_movie'),
    path('user/<int:other_id>/library/edit_movie&<str:movie_id>', views.edit_movie, name='edit_movie'),
    path('user/<int:other_id>/view', views.view_profile, name = 'view_profile'),
    path('user/<int:other_id>/request_sent', views.send_friend_request, name = 'request_sent'),
    path('user/<int:other_id>/request_cancelled', views.cancel_friend_request, name = 'request_cancelled'),
    path('user/<int:other_id>/request_accepted', views.add_friend, name = 'request_accepted'),
    path('user/<int:other_id>/remove_friend', views.remove_friend, name = 'remove_friend'),
    path('user/list_friends', views.list_friends, name='list_friends'),
    path('user/messages', views.messages, name='messages'),
    path('user/change_password', views.change_password, name='change_password'),
    path('user/preferences', views.set_user_preferences, name='set_user_preferences'),
    path('find_friends/index', views.find_friend_index, name = 'find_friend_index'),
    path('find_friends/results', views.find_friend_results, name = 'find_friend_results'),
    path('search', views.search, name='search'),
    path('browse', views.browse, name='browse'),
    path('movie/<str:movie_id>/send_borrow_request', views.send_borrow_request, name='send_borrow_request'),
    path('movie/<int:borrow_request_id>/update_borrow_request', views.update_borrow_request, name='update_borrow_request'),
]

# account views -- to get to /login, href="/login"
# accounts/login/ [name='login']
# accounts/logout/ [name='logout']
# accounts/password_change/ [name='password_change']
# accounts/password_change/done/ [name='password_change_done']
# accounts/password_reset/ [name='password_reset']
# accounts/password_reset/done/ [name='password_reset_done']
# accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
# accounts/reset/done/ [name='password_reset_complete']
