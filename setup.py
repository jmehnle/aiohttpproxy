import os
import re
from setuptools import setup

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
        'lib', 'aiohttpproxy', '__init__.py'), 'r') as f:
    try:
        version = re.findall(r"^__version__ = '([^']+)'$", f.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version')

install_requires = ['aiohttp']

tests_require = install_requires + ['nose']

setup(
    name                = 'aiohttpproxy',
    version             = version,
    description         = 'Simple aiohttp HTTP Proxy',
    url                 = 'https://github.com/jmehnle/aiohttpproxy',
    author              = 'Julian Mehnle',
    author_email        = 'julian@mehnle.net',
    license             = 'Apache-2.0',
    package_dir         = {'': 'lib'},
    packages            = ['aiohttpproxy'],
    install_requires    = install_requires,
    tests_require       = tests_require,
    test_suite          = 'nose.collector',
    scripts             = ['bin/aiohttpproxy']
)

# vim:sw=4 sts=4
