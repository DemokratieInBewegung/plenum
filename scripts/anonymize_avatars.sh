#!/bin/bash
set -e

# before running this script, check out a version that sets AVATAR_EXPOSE_USERNAMES = False
docker-compose build web
docker-compose stop web
tar cvfz data.tgz data # backup
docker-compose run web python manage.py anonymize_avatars
docker-compose up -d web
