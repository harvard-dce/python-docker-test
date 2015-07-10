# -*- coding: utf-8 -*-

import sys
from time import sleep
import docker
from docker.errors import APIError
from requests import ConnectionError, Session

class ConfigurationError(Exception):
    pass

class CanvasDockerTestMixin(object):

    def setUp(self):

        if not hasattr(self, 'DOCKER_IMAGE'):
            raise ConfigurationError("Test class missing DOCKER_IMAGE attribute")

        try:
            self.docker = docker.Client(version='auto')
            self.docker.ping()
        except ConnectionError, e:
            print >>sys.stderr, "Can't connect to docker. Is it installed/running?"
            raise

        self.session = Session()
        self.session.headers.update({'Authorization': 'Bearer canvas-docker'})

        try:
            self._start()
        except APIError, e:
            if '404' in str(e.message):
                print >>sys.stderr, "%s image not found; pulling..." % self.DOCKER_IMAGE
                self._pull_image()
                self._start()
            else:
                raise

    def tearDown(self):
        self._stop_rm()

    def api_url(self, path):
        return self.canvas_api_base + path

    def _pull_image(self):
        result = self.docker.pull(self.DOCKER_IMAGE)
        if 'error' in result:
            raise ConfigurationError(result['error'])

    def _start(self):

        self._container = self.docker.create_container(
            self.DOCKER_IMAGE,
            name='canvas-docker',
            ports=[3000, 5432],
        )
        self.docker.start(self._container)
        self.addCleanup(self._stop_rm)

        container_info = self.docker.inspect_container(self._container)
        self.container_ip = container_info['NetworkSettings']['IPAddress']
        self.docker_gateway_ip = container_info['NetworkSettings']['Gateway']
        self.canvas_api_base = 'http://{}:3000/api/v1'.format(self.container_ip)

        self._wait_for_canvas()

    def _wait_for_canvas(self):
        tries = 10
        print >>sys.stderr, "Waiting for canvas to start..."
        while tries > 0:
            try:
                print >>sys.stderr, "Number of tries left: {}".format(tries)
                resp = self.session.head(self.canvas_api_base + '/accounts/1')
                assert resp.status_code == 200
                return
            except ConnectionError:
                tries -= 1
                sleep(20)
        raise


    def _stop_rm(self):
        if hasattr(self, '_container'):
            self.docker.stop(self._container)
            self.docker.remove_container(self._container)
            delattr(self, '_container')

