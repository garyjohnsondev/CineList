from urllib.parse import urlparse
from django.urls import resolve
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
import requests

api_root = 'https://api.themoviedb.org/3'
api_key = '0ba059be682204c1870cf30296aa5ddf'

def tmdb_search(request, reject_if_404=True):
    url = api_root + '/discover/movie'
    params = dict(request.GET.dict())
    params.update(dict(api_key=api_key, language='en-US', sort_by='popularity.desc', include_adult=False, include_video=False))

    if params['query'] is None or params['query'].strip() == '':
        params.remove('query')
    else:
        promise = requests.get(url, params=params)

    if promise.status_code != 200:
        reject(request)
    return promise.json()

def get_tmdb_movie(request, id, reject_if_404=True):
    url = api_root + '/movie/' + str(id)
    params = dict(request.GET.dict())
    params.update(dict(api_key=api_key, language='en-US', append_to_response='release_dates'))
    promise = requests.get(url, params=params)

    if promise.status_code != 200:
        reject(request)
    return promise.json()

def get_genres():
    '''
    For whatever reason, this request never resolves, even on other platforms (i.e. React Native).
    Docs at https://developers.themoviedb.org/3/genres/get-movie-list
    '''
    promise = requests.get(api_root + '/genres/movie/list' + api_key + '&language=en-US')
    return promise.json()

def get_trending():
    promise = requests.get(api_root + '/trending/movie/week' + api_key)
    if promise == 200:
        return promise.json()
    else:
        pass

def reject(request, responseJson):
    messages.add_message(request, messages.ERROR, responseJson['status_message'])

    next = request.META.get('HTTP_REFERER', None) or '/user/dashboard'
    response = HttpResponseRedirect(next)

    view, args, kwargs = resolve(urlparse(next)[2])
    kwargs['request'] = request
    try:
        view(*args, **kwargs)
    except Http404:
        return HttpResponseRedirect('/user/dashboard')
    return response
