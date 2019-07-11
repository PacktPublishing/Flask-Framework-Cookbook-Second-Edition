#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
from setuptools import setup

setup(
    name = 'my_app',
    version='1.0',
    license='GNU General Public License v3',
    author='Shalabh Aggarwal',
    author_email='contact@shalabhaggarwal.com',
    description='Catalog application for Flask',
    packages=[
        'my_app',
        'my_app.catalog',
    ],
    platforms='any',
    install_requires=[
        'Flask>=0.10.1',
        'flask-sqlalchemy',
        'flask-wtf',
        'flask-babel',
        'sentry-sdk',
        'blinker',
        'geoip2',
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3', 
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    zip_safe = False,
)
