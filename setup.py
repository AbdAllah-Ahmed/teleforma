# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
import teleforma

CLASSIFIERS = ['Environment :: Web Environment', 'Framework :: Django', 'Intended Audience :: Science/Research', 'Intended Audience :: Education', 'Programming Language :: Python', 'Programming Language :: JavaScript', 'Topic :: Internet :: WWW/HTTP :: Dynamic Content', 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application', 'Topic :: Multimedia :: Sound/Audio', 'Topic :: Multimedia :: Sound/Audio :: Analysis', 'Topic :: Multimedia :: Sound/Audio :: Players', 'Topic :: Scientific/Engineering :: Information Analysis', 'Topic :: System :: Archiving',  ]

README = os.path.join(os.path.dirname(__file__), 'README.rst')

setup(
  name = "TeleForma",
  url = "http://parisson.com/products/teleforma",
  description = "open multimedia e-leaning system",
  long_description = open(README).read(),
  author = "Guillaume Pellerin",
  author_email = "yomguy@parisson.com",
  version = teleforma.__version__,
  install_requires = [
        'django>=1.3.1',
        'telemeta',
        'south',
        'django-pagination',
        'django-postman',
        'django-extensions',
  ],
  platforms=['OS Independent'],
  license='CeCILL v2',
  classifiers = CLASSIFIERS,
  packages = find_packages(),
  include_package_data = True,
  zip_safe = False,
)
