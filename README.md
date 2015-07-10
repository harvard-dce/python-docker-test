## canvas-docker-test

A unittest.TestCase mixin for executing integration/acceptance tests against a Docker-ized Canvas instance.

### Running your app server

In order for your app to visible from the containerized Canvas instance you must bind the app server to Docker's gateway ip (default: 172.17.42.1).

In django:

`python manage.py runserver 172.17.42.1:8000`
