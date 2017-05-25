#!/bin/bash
set -e
cd /code

# Build static files
echo "Collecting statics" 
SECRET_KEY=temp_value python manage.py collectstatic -v 0 --clear --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

echo "------ Upgrade done -----"