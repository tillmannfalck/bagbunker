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

import datetime
import json
from werkzeug.datastructures import Headers
from ..storage import Fileset
from ..testing import FlaskTestCase, db


class TestCase(FlaskTestCase):
    def setUp(self):
        db.session.add(Fileset(
            md5='deadbeef',
            storage_id=1,
            name='fakeset',
            dirpath='/foo',
            type='bag',
            time_added=datetime.datetime.utcnow(),
            time_updated=datetime.datetime.utcnow(),
        ))
        db.session.add(Fileset(
            md5='beefbeef',
            storage_id=1,
            name='another fakeset',
            dirpath='/foo',
            type='bag',
            time_added=datetime.datetime.utcnow(),
            time_updated=datetime.datetime.utcnow(),
        ))
        db.session.commit()

    def get(self, *args, **kw):
        kw.setdefault('content_type', 'application/vnd.api+json')
        return self.client.get(*args,
                               headers=Headers([('Accept', 'application/json')]),
                               **kw)

    def post(self, *args, **kw):
        kw.setdefault('content_type', 'application/vnd.api+json')
        return self.client.post(*args,
                                headers=Headers([('Accept', 'application/json')]),
                                **kw)

    def test_comment(self):
        resp = self.get('/marv/api/comment')
        self.assert200(resp)
        self.assertEqual(resp.json['meta']['total'], 0)

        self.login()

        resp = self.get('/marv/api/comment')
        self.assert200(resp)
        self.assertEqual(resp.json['meta']['total'], 0)

        resp = self.get('/marv/api/fileset')
        self.assert200(resp)
        self.assertEqual(resp.json['meta']['total'], 2)

        resp = self.post('/marv/api/comment', data=json.dumps({
            "data": {"attributes": {"text": "test comment", "timestamp": None},
                     "relationships": {"author": {"data": {"type": "user", "id": "1"}},
                                       "fileset": {"data": {"type": "fileset",
                                                            "id": "1"}}},
                     "type": "comment"}
        }))
        self.assertStatus(resp, 201)
        self.assertTrue(resp.json)
        self.assertTrue(resp.json['data']['attributes']['timestamp'])

        resp = self.get('/marv/api/comment')
        self.assert200(resp)
        self.assertEqual(resp.json['meta']['total'], 1)

        resp = self.post('/marv/api/comment', data=json.dumps({
            "data": {"attributes": {"text": "test comment", "timestamp": None},
                     "relationships": {"author": {"data": {"type": "user", "id": "1"}},
                                       "fileset": {"data": {"type": "fileset",
                                                            "id": "1"}}},
                     "type": "comment"}
        }))
        self.assertStatus(resp, 201)
        self.assertTrue(resp.json)
        self.assertTrue(resp.json['data']['attributes']['timestamp'])

        resp = self.get('/marv/api/comment')
        self.assert200(resp)
        self.assertEqual(resp.json['meta']['total'], 2)

        self.logout()

        resp = self.get('/marv/api/comment')
        self.assert200(resp)
        self.assertEqual(resp.json['meta']['total'], 2)

    def test_comment_no_auth(self):
        resp = self.post('/marv/api/comment', data=json.dumps({
            'fileset_id': 1,
            'author_id': 1,
            'text': 'foo',
        }))
        self.assert401(resp)
