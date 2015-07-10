import os
import re
import codecs
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

def read(path):
    return codecs.open(os.path.join(here, path), 'r', 'utf-8').read()

version_file = read('canvas_docker_test/__init__.py')
version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M).group(1)

setup(
    name='canvas-docker-test',
    version=version,
    description='unittest.TestCase mixin for executing integration tests against canvas-docker',
    author='Jay Luker',
    author_email='jay_luker@harvard.edu',
    url='https://github.com/harvard-dce/canvas-docker-test',
    packages=find_packages(),
    install_requires=[''],
    license='MIT License',
    keywords='canvas lms lti',
    zip_safe=True
)
