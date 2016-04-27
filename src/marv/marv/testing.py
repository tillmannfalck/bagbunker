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

import bcrypt
import flask.ext.testing
import functools
import hashlib
import inspect
import os
import shutil
import tempfile

from . import create_app
from . import settings
from .model import db
from .site import Site


def create_tempdir():
    d = tempfile.mkdtemp()

    def cleanup():
        shutil.rmtree(d)
    return d, cleanup


def default_from_self(f):
    @functools.wraps(f)
    def method(self, **provided_kw):
        args = inspect.getargspec(f).args
        kw = dict()
        for k in args[1:]:
            v = provided_kw.pop(k, None)
            kw[k] = v if v is not None else getattr(self, k)
        return f(self, **kw)
    return method


def ls(path):
    return list(sorted(os.listdir(path)))


def make_fileset(directory, format='foo', parts=3, set_idx=0,
                 prefix=None, empty_idx=None, missing_idx=None,
                 missing_md5_idx=None, content_template=None,
                 template='set%(set_idx)s.file%(file_idx)s.%(format)s'):
    for i in range(parts):
        if i == missing_idx:
            continue

        if prefix is not None:
            template = '{}{}'.format(prefix, template)
        if content_template is None:
            content_template = 'content_{}'.format(template)

        substitutions = dict(set_idx=set_idx, file_idx=i, format=format)
        filename = template % substitutions
        path = os.path.join(directory, filename)
        content = content_template % substitutions if i != empty_idx else ''
        with open(path, 'wb') as f:
            f.write(content)

        if i != missing_md5_idx:
            md5 = hashlib.md5(content).hexdigest()
            with open('{}.md5'.format(path), 'wb') as f:
                f.write('{}  {}'.format(md5, filename))


# list md5s of a storage on filesystem
def list_nondot(path):
    return [x for x in sorted(os.listdir(path)) if x[0] != '.']


DEFAULT_USERNAME = 'm'
DEFAULT_PASSWORD = 'm'


class FlaskTestCase(flask.ext.testing.TestCase, settings.Testing):
    def __call__(self, result=None):
        # flask.ext.testing.TestCase catches exceptions in _pre_setup
        # and create_app ...
        try:
            self._pre_setup()
            # we skip one
            super(flask.ext.testing.TestCase, self).__call__(result)
        except:
            import sys
            import traceback
            traceback.print_exc(file=sys.stdout)
        finally:
            self._post_teardown()

    def create_app(self):
        instance_path, self.instance_cleanup = create_tempdir()
        Site(instance_path).init_root()
        if self.DB_SQLITE:
            shutil.copy2(self.DB_SQLITE, instance_path)
            self.SQLALCHEMY_DATABASE_URI = \
                'sqlite:///{path}/db.sqlite'.format(path=instance_path)
        with open(os.sep.join([instance_path, 'users.txt']), 'wb') as f:
            f.write('{}:{}\n'.format(
                DEFAULT_USERNAME,
                bcrypt.hashpw(DEFAULT_PASSWORD, bcrypt.gensalt())
            ))
        return create_app(self, INSTANCE_PATH=instance_path)

    def _pre_setup(self):
        super(FlaskTestCase, self)._pre_setup()
        if self.DB_CREATE_ALL:
            db.create_all()

    def _post_teardown(self):
        db.session.remove()
        db.drop_all()
        self.instance_cleanup()
        super(FlaskTestCase, self)._post_teardown()

    def login(self, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD):
        return self.client.post('/marv/api/_login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/marv/api/_logout', follow_redirects=True)
