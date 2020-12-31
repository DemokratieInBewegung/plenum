#!/bin/bash
set -e
cd /code

# Build static files
echo "Collecting statics" 
SECRET_KEY=temp_value python manage.py collectstatic -v 0 --clear --noinput

# Create local database migrations
echo "Create database migrations"
python manage.py makemigrations

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

echo "Creating new revisions"
python manage.py createinitialrevisions --comment "Erste Fassung"

echo "------ Upgrade done -----"