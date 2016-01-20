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

import os


host = os.environ.get('PGHOSTADDR')
user = os.environ.get('PGUSER')
password = os.environ.get('PGPASSWORD')
POSTGRESQL_URI = 'postgresql://{}:{}@{}/bagbunker'.format(user, password, host)


class _Base(object):
    # XXX: set to True after ugrade to 2.1 to silence warnings
    # Needs evaluation whether False is ok for us.
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class Development(_Base):
    DEVELOPMENT = True
    SQLALCHEMY_DATABASE_URI = POSTGRESQL_URI


class Production(_Base):
    PRODUCTION = True
    USE_X_SENDFILE = True
    SQLALCHEMY_DATABASE_URI = POSTGRESQL_URI


class Testing(_Base):
    MARV_SIGNAL_URL = None
    SQLALCHEMY_ECHO = bool(os.environ.get('SQLALCHEMY_ECHO', False))
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    DB_SQLITE = None
    TESTING = True
    DB_CREATE_ALL = True
