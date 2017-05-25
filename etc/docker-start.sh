#!/bin/bash

cd /code

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting server"
gunicorn -w 3 -b 0.0.0.0 voty.wsgi