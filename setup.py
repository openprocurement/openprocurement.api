import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

requires = [
    'barbecue',
    'chaussette',
    'cornice',
    'couchdb-schematics',
    'gevent',
    'iso8601',
    'jsonpatch',
    'libnacl',
    'pbkdf2',
    'pycrypto',
    'pyramid_exclog',
    'requests',
    'rfc6266',
    'setuptools',
    'tzlocal',
]
test_requires = requires + [
    'webtest',
    'python-coveralls',
    'mock'
]
docs_requires = requires + [
    'sphinxcontrib-httpdomain',
]

entry_points = {
    'paste.app_factory': [
        'main = openprocurement.api.app:main'
    ],
    'openprocurement.api.plugins': [
        'api = openprocurement.api.includeme:includeme'
    ],
    'openprocurement.api.migrations': [
        'tenders = openprocurement.api.migration:migrate_data'
    ],
    'console_scripts': [
        'bootstrap_api_security = openprocurement.api.database:bootstrap_api_security'
    ]
}

setup(name='openprocurement.api',
      version='2.4.1',
      description='openprocurement.api',
      long_description=README,
      classifiers=[
          "Framework :: Pylons",
          "License :: OSI Approved :: Apache Software License",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
      ],
      keywords="web services",
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      url='https://github.com/openprocurement/openprocurement.api',
      package_dir={'': 'src'},
      py_modules=['cgi'],
      packages=find_packages('src'),
      namespace_packages=['openprocurement'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'test': test_requires, 'docs': docs_requires},
      test_suite="openprocurement.api.tests.main.suite",
      entry_points=entry_points)
