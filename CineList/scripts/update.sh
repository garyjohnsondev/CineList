#!/bin/bash

python manage.py flush --no-input
python manage.py makemigrations main
python manage.py migrate
python manage.py loaddata test_data.json

python manage.py runserver
