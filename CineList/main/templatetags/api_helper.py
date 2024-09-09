from django.template import Library
import requests
from main.services import get_tmdb_movie
register = Library()

root = 'https://api.themoviedb.org/3';
api_key = '?api_key=0ba059be682204c1870cf30296aa5ddf'
tmdbImageURL = "http://image.tmdb.org/t/p/w185/";
placeholderImgURL= "https://s3-ap-southeast-1.amazonaws.com/popcornsg/placeholder-movieimage.png";

@register.filter(name='tmdb_image')
def tmdb_image(image_path):
    if image_path is None:
        return placeholderImgURL
    else:
        return tmdbImageURL + image_path

@register.filter(name='get_background_img')
def get_background_img(tmdb_id):
    responseJson, status = get_tmdb_movie(tmdb_id)
    return tmdbImageURL + responseJson['backdrop_path']
