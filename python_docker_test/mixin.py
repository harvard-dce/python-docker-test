# -*- coding: utf-8 -*-

import sys
import threading
from time import sleep
import docker
from docker.errors import APIError
from requests import ConnectionError

__all__ = ['PythonDockerTestMixin', 'ConfigurationError', 'ContainerNotReady']

DEFAULT_READY_TRIES = 10
DEFAULT_READY_SLEEP = 3

class ConfigurationError(Exception):
    pass

class ContainerNotReady(Exception):
    pass

class ContainerStartThread(threading.Thread):

    def __init__(self, image, ready_callback, ready_tries, ready_sleep):
        self.is_ready = threading.Event()
        self.error = None
        self.image = image
        self.ready_tries = ready_tries
        self.ready_sleep = ready_sleep
        self.ready_callback = ready_callback
        super(ContainerStartThread, self).__init__()

    def run(self):

        try:
            try:
                self.client = docker.Client(version='auto')
                self.client.ping()
            except ConnectionError, e:
                self.error = "Can't connect to docker. Is it installed/running?"
                raise

            # confirm that the image we want to run is present and pull if not
            try:
                self.client.inspect_image(self.image)
            except APIError, e:
                if '404' in str(e.message):
                    print >>sys.stderr, "%s image not found; pulling..." % self.image
                    result = self.client.pull(self.image)
                    if 'error' in result:
                        raise ConfigurationError(result['error'])

            # create and start the container
            self.container = self.client.create_container(self.image)
            self.client.start(self.container)
            self.container_data = self.client.inspect_container(self.container)

            if self.ready_callback is not None:
                # wait for the container to be "ready"
                print >>sys.stderr, "Waiting for container to start..."
                tries = self.ready_tries
                while tries > 0:
                    try:
                        print >>sys.stderr, "Number of tries left: {}".format(tries)
                        self.ready_callback(self.container_data)
                        break
                    except ContainerNotReady:
                        tries -= 1
                        sleep(self.ready_sleep)

            self.is_ready.set()

        except Exception, e:
            self.exc_info = sys.exc_info()
            if self.error is None:
                self.error = e.message
            self.is_ready.set()


    def terminate(self):
        if hasattr(self, 'container'):
            self.client.stop(self.container)
            self.client.remove_container(self.container)



class PythonDockerTestMixin(object):

    @classmethod
    def setUpClass(cls):
        """
        Checks that image
        defined in cls.CONTAINER_IMAGE is present and pulls if not. Starts
        the container in a separate thread to allow for better cleanup if
        exceptions occur during test setup.
        """
        if not hasattr(cls, 'CONTAINER_IMAGE'):
            raise ConfigurationError("Test class missing CONTAINER_IMAGE attribute")

        ready_tries = getattr(cls, 'CONTAINER_READY_TRIES', DEFAULT_READY_TRIES)
        ready_sleep = getattr(cls, 'CONTAINER_READY_SLEEP', DEFAULT_READY_SLEEP)
        ready_callback = getattr(cls, 'container_ready_callback')

        cls.container_start_thread = ContainerStartThread(
            cls.CONTAINER_IMAGE, ready_callback, ready_tries, ready_sleep
        )
        cls.container_start_thread.daemon = True
        cls.container_start_thread.start()

        # wait for the container startup to complete
        cls.container_start_thread.is_ready.wait()
        if cls.container_start_thread.error:
            # Clean up behind ourselves, since tearDownClass won't get called in
            # case of errors.
            cls._tearDownClassInternal()
            raise cls.container_start_thread.exc_info[1], None, cls.container_start_thread.exc_info[2]

        cls.container_data = cls.container_start_thread.container_data

        super(PythonDockerTestMixin, cls).setUpClass()


    @classmethod
    def _tearDownClassInternal(cls):
        if hasattr(cls, 'container_start_thread'):
            cls.container_start_thread.terminate()
            cls.container_start_thread.join()
            delattr(cls, 'container_start_thread')

    @classmethod
    def tearDownClass(cls):
        super(PythonDockerTestMixin, cls).tearDownClass()
        cls._tearDownClassInternal()

    def setUp(self):
        self.container_ip = self.container_data['NetworkSettings']['IPAddress']
        self.docker_gateway_ip = self.container_data['NetworkSettings']['Gateway']

