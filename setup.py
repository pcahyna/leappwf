""" LeApp WorkFlow module """

from codecs import open
from distutils.util import convert_path
from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

_NAME = None
_VERSION = None

with open(convert_path('leappwf/version.py')) as mod:
    ns = {}
    exec(mod.read(), ns)
    _NAME = ns['__pkg_name__']
    _VERSION = ns['__version__']

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=_NAME,
    version=_VERSION,

    description='LeApp WorkFlow module',
    long_description=long_description,
    url='http://github.com/...',

    author='Red Hat',
    author_email='leap-devel@redhat.com',

    license='LGPLv2+',

    packages=['leappwf'],

    zip_safe=False,
)
