#!/bin/bash
set -e

git fetch
git checkout $TRAVIS_BRANCH
docker compose build web
docker compose run web bash /code/scripts/upgrade.sh
docker compose stop web
docker compose up -d web 
