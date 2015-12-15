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

    def test_tag_no_fileset(self):
        self.login()

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': -1,
                                 'tag_label': 'foo',
                             }))
        self.assertEqual(response.status_code, 400)

    def test_tag_no_label_or_id(self):
        self.login()

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                             }))
        self.assertEqual(response.status_code, 400)

    def test_tag_unknown_id(self):
        self.login()

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_id': 42,
                             }))
        self.assertEqual(response.status_code, 400)

    def test_tag(self):
        self.login()

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_label': 'foo',
                             }))
        self.assert200(response)
        self.assertEqual(response.json['label'], 'foo')
        self.assertEqual(response.json['id'], 1)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(len(tags), 1)

        # post same tag again - no change
        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_label': 'foo',
                             }))
        self.assert200(response)
        self.assertEqual(response.json['label'], 'foo')
        self.assertEqual(response.json['id'], 1)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [{u'type': u'tag', u'id': u'1'}])

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_label': 'bar',
                             }))
        self.assert200(response)
        self.assertEqual(response.json['label'], 'bar')
        self.assertEqual(response.json['id'], 2)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [{'type': 'tag', 'id': '1'},
                                {'type': 'tag', 'id': '2'}])

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_id': 2,
                             }))
        self.assert200(response)
        self.assertEqual(response.json['label'], 'bar')
        self.assertEqual(response.json['id'], 2)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [{'type': 'tag', 'id': '1'},
                                {'type': 'tag', 'id': '2'}])

        response = self.get('/marv/api/tag')
        self.assert200(response)
        self.assertEqual(response.json['meta']['total'], 2)

    def test_untag_no_fileset(self):
        self.login()

        response = self.post('/marv/api/_untag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': -1,
                                 'tag_label': 'foo',
                             }))
        self.assertEqual(response.status_code, 400)

    def test_untag_no_label_or_id(self):
        self.login()

        response = self.post('/marv/api/_untag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                             }))
        self.assertEqual(response.status_code, 400)

    def test_untag_unknown_id(self):
        self.login()

        response = self.post('/marv/api/_untag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_id': 42,
                             }))
        self.assertEqual(response.status_code, 400)

    def test_untag_unknown_label(self):
        self.login()

        response = self.post('/marv/api/_untag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_label': 'foo',
                             }))
        self.assertEqual(response.status_code, 400)

    def test_untag(self):
        self.login()

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_label': 'foo',
                             }))
        self.assert200(response)
        self.assertEqual(response.json['label'], 'foo')
        self.assertEqual(response.json['id'], 1)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [{'type': 'tag', 'id': '1'}])

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 2,
                                 'tag_label': 'foo',
                             }))
        self.assert200(response)
        self.assertEqual(response.json['label'], 'foo')
        self.assertEqual(response.json['id'], 1)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [{'type': 'tag', 'id': '1'}])

        response = self.post('/marv/api/_tag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_label': 'bar',
                             }))
        self.assert200(response)
        self.assertEqual(response.json['label'], 'bar')
        self.assertEqual(response.json['id'], 2)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [{'type': 'tag', 'id': '1'},
                                {'type': 'tag', 'id': '2'}])

        response = self.post('/marv/api/_untag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_label': 'bar',
                             }))
        self.assert200(response)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [{'type': 'tag', 'id': '1'}])

        response = self.get('/marv/api/tag')
        self.assert200(response)
        self.assertEqual(response.json['meta']['total'], 1)

        response = self.post('/marv/api/_untag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_id': 1,
                             }))
        self.assert200(response)

        response = self.get('/marv/api/fileset/1')
        self.assert200(response)
        tags = response.json['data']['relationships']['tags']['data']
        self.assertEqual(tags, [])

        response = self.post('/marv/api/_untag',
                             content_type='application/json',
                             data=json.dumps({
                                 'fileset_id': 1,
                                 'tag_id': 1,
                             }))
        self.assert200(response)

        response = self.get('/marv/api/tag')
        self.assert200(response)
        self.assertEqual(response.json['meta']['total'], 1)
