#!/bin/bash

# PACKAGES
pip install psycopg2-binary
pip install django-crispy-forms

# FRESH DB INSTALL
dropdb cinelist_dev
createdb cinelist_dev
python manage.py makemigrations main
python manage.py migrate
python manage.py loaddata test_data.json

python manage.py runserver
