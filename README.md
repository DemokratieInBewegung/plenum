# Voty - The Voting Platform of [DEMOKRATIE IN BEWEGUNG](https://bewegung.jetzt)

#### Travis Build Status

##### Master
[![Build Status](https://travis-ci.org/DemokratieInBewegung/abstimmungstool.svg?branch=master)](https://travis-ci.org/DemokratieInBewegung/abstimmungstool)

##### Develop
[![Build Status](https://travis-ci.org/DemokratieInBewegung/abstimmungstool.svg?branch=develop)](https://travis-ci.org/DemokratieInBewegung/abstimmungstool)

## Development 

This runs on Python Django. For Development, you'll need Python 3.0 and a virtual environment.

To install the packages required for a successful install on Ubuntu, run

```
sudo apt-get install python3-dev
sudo apt-get install virtualenv
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install libpq-dev
sudo apt-get install libjpeg8-dev
```

On Mac OS X, run

```
brew install python3
sudo easy_install pip
sudo pip install virtualenv
brew update
brew install postgres
 ```

1. Set up your local Virtual environment

```
virtualenv -p python3 .   # setup a new virtual environment locally
source bin/activate       # enter that environment: needs to happen for every shell session!
```

2. From within the enviroment install the dependencies

```
pip install -r requirements.txt
```

3. (create and) update the database
```
python manage.py migrate pinax_notifications
python manage.py migrate initproc 0009
python manage.py migrate
```

4. Set a quorum
```
python manage.py set_quorum
```

5. Create a super user
```
python manage.py createsuperuser
```

6. Generate some random initiatives (all in pre-visible state)

```
python manage.py shell -c "from voty.initproc.helpers import generate_initiative_from_random_wikipedia_article; generate_initiative_from_random_wikipedia_article()"
```

(Run this multiple times for multiple Initiatives)

7. Start the server
```
python manage.py runserver
```

8. Go to the browser

The server will host the instance at http://localhost:8000/ . The Admin-Interface (you generated an account for in 4) is available at http://localhost:8000/admin/ . Within that just navigate to the "Initiative"(s) and change the state of some of them to make the available and view them in said state.

This server automatically refreshes when you change the python source code or the html templates. 

Happy Hacking!


## To update the local checkout do:

```
git pull
source bin/activate
pip install -r requirements.txt
python manage.py migrate
```



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

### Deployment cycle

This project runs on a continuous integration schedule with the premise "master is always live". Meaning that whenever something is pushed to master, this will immediately deployed on [abstimmen.bewegung.jetzt](https://abstimmen.bewegung.jetzt) and will go live. So, whatever you see here, is what is live.

As for that, pushing and commiting to master is restricted. And usual development should go against the `develop` branch where everything ought to be merged before that being merged into `master`. But also here we have a continous integration process: everything on `develop` will immediately deploy on the testing instance at [abstimmen-beta.bewegung.jetzt](https://abstimmen-beta.bewegung.jetzt/).

Therefore, any bigger changes are recommended to handle in your own branch outright and merge that against develop, test those on the beta and only then merge and push them on master for real-live deployment.

In short:

  my-branch --PR-> develop --PR-> master


## Frontend Testing

![BrowserStack](http://i.imgur.com/Eqx1QcB.png)

We're using [BrowserStack](https://www.browserstack.com/) to test and ensure a consistent rendering of Voty across all modern browsers and mobile devices.


## License

This is released under AGPL-3.0. See the LICENSE-file for the full text.
