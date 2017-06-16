#!/bin/bash
set -e

git pull
docker-compose build web
docker-compose run web bash /code/scripts/upgrade.sh
docker-compose stop web
docker-compose up -d web 
