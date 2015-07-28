## python-docker-test

A unittest.TestCase mixin for executing integration/acceptance tests against 
containerized services.

### Running your app server

In order for your app to visible from the container you must bind the app server
to it's gateway ip (default: 172.17.42.1).

In django:

`python manage.py runserver 172.17.42.1:8000`
