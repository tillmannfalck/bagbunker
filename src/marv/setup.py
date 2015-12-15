# -*- coding: utf-8 -*-
#
# Copyright 2015 Ternaris, Munich, Germany
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import absolute_import, division

from setuptools import setup

# here = os.path.abspath(os.path.dirname(__file__))
# with open(os.path.join(here, 'README.txt')) as f:
#     README = f.read()
# with open(os.path.join(here, 'CHANGES.txt')) as f:
#     CHANGES = f.read()

requires = [
    'alembic',
    'click',
    'flask-compress',
    'Flask-Cors',       # For development
    'Flask-Login',
    'Flask-Testing',    # for tests
    'Flask-Restless',
    'Flask-SQLAlchemy',
    'ipdb',             # for job development
    'psycopg2',
    'py-bcrypt',
    'pysqlite',
    'pytz',
    'testfixtures',     # for tests

    # Testing
    'nose',
    'coverage',
    'ipdbplugin',
    ]

setup(name='marv',
      version='1.0.dev0',
      # description='',
      # long_description=README + '\n\n' + CHANGES,
      # FIXME: Add classifiers
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 2 :: Only",
          "Programming Language :: Python :: Implementation :: CPython",
          "Framework :: Flask",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
          "Topic :: Scientific/Engineering",
      ],
      author='Ternaris',
      author_email='team@ternaris.com',
      url='',
      license='MIT',
      keywords='web wsgi flask',  # FIXME: Are there ROS specific keywords?
      packages=['marv'],
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'],
      install_requires=requires,
      entry_points={
      })
