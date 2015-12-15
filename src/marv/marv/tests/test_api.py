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

from werkzeug.datastructures import Headers
from ..testing import FlaskTestCase


class TestCase(FlaskTestCase):
    def get(self, *args, **kw):
        return self.client.get(*args,
                               headers=Headers([
                                   ('Accept', 'application/json'),
                                   ('Content-Type', 'application/vnd.api+json"')]),
                               **kw)

    def test_empty(self):
        self.login()
        resp = self.get('/marv/api/storage')
        self.assert200(resp)
        resp = self.get('/marv/api/file')
        self.assert200(resp)
        resp = self.get('/marv/api/fileset')
        self.assert200(resp)
        resp = self.get('/marv/api/_fileset-detail')
        self.assert200(resp)
        resp = self.get('/marv/api/_fileset-detail-by-md5')
        self.assert200(resp)
        resp = self.get('/marv/api/_fileset-listing')
        self.assert200(resp)
        resp = self.get('/marv/api/_fileset-summary')
        self.assert200(resp)
        resp = self.get('/marv/api/_webconfig')
        self.assert200(resp)
