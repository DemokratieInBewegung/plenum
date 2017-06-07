# Voty - the Voting Platform of [DEMOKRATIE IN BEWEGUNG](https://bewegung.jetzt)

## Development 

This runs on Python Django. For Development, you'll need Python 3.0 and a virtual environment.

1. Set up your local Virtual environment

```
virtualenv -P python3 .   # setup a new virtual environment locally
source bin/activate       # enter that environment: needs to happen for every shell session!
```

2. From within the enviroment install the dependencies

```
pip install -r requirements.txt
```

3. (create and) update the database
```
python manage.py migrate
```

4. Create a super user
```
python manage.py createsuperuser
```

5. Generate some random initiatives (all in pre-visible state)

```
python manage.py shell -c "from voty.initproc.helpers import generate_initiative_from_random_wikipedia_article; generate_initiative_from_random_wikipedia_article()"
```

(Run this multiple times for multiple Initiatives)

6. Start the server
```
python manage.py runserver
```

7. Go to the browser

The server will host the instance at http://localhost:8000/ . The Admin-Interface (you generated an account for in 4) is available at http://localhost:8000/admin/ . Within that just navigate to the "Initiative"(s) and change the state of some of them to make the available and view them in said state.

This server automatically refreshes when you change the python source code or the html templates. 

Happy Hacking!

## Frontend Testing

![BrowserStack](http://imgur.com/a/upHPK)

We're using Browserstack to test and ensure a consistent rendering of Voty across all modern browsers and mobile devices.

## Deployment

Using docker-compose, right from within this repo, run:

```
docker compose up
```

### Upgrade database

Don't forget to update the database after/within each deploy:

```
docker compose exec web bash /code/scripts/upgrade.sh
```

## License

This released under AGPL-3.0 . See the LICENSE-file for the full text.
