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
from flask import json, url_for
from pkg_resources import resource_filename

from werkzeug.datastructures import Headers
from marv.registry import load_formats, load_jobs
from marv.testing import FlaskTestCase

# XXX: not good!
load_formats()
load_jobs()


class TestCase(FlaskTestCase):
    DB_SQLITE = resource_filename(__name__, os.path.join('replay', 'db.sqlite'))
    RECORD = os.environ.get('BAGBUNKER_REPLAY_TEST_RECORD', None)

    def get(self, *args, **kw):
        return self.client.get(*args,
                               content_type='application/vnd.api+json',
                               headers=Headers([('Accept', 'application/json')]),
                               **kw)

    def runReplay(self, name, data=None):
        relative = os.path.join('replay', '{}.json'.format(name.replace('/', '_')))
        fullpath = resource_filename(__name__, relative)
        if data:
            url = url_for('%s' % name, **data)
        else:
            url = '/marv/api/%s' % name
        res = self.get(url)
        if res.status_code >= 300:
            result = res.status_code
        else:
            result = json.loads(res.data)
        if self.RECORD:
            reference = result
            with open(fullpath, 'wb') as f:
                f.write(json.dumps(result, indent=2, sort_keys=True))
                f.seek(0)
            self.skipTest('Recording')
        else:
            with open(fullpath, 'rb') as f:
                reference = json.load(f)
        return reference, result

    def test_detail(self):
        reference, result = self.runReplay('_fileset-detail')
        self.maxDiff = None
        self.assertEquals(reference, result)

    def test_detail_1(self):
        reference, result = self.runReplay('_fileset-detail/1')
        self.maxDiff = None
        self.assertEquals(reference, result)

    def test_detail_by_md5(self):
        reference, result = self.runReplay(
            '_fileset-detail-by-md5/28b6a7839c69dc9adff31676bedf39ba')
        self.maxDiff = None
        self.assertEquals(reference, result)

    def test_listing(self):
        reference, result = self.runReplay('_fileset-listing')
        self.maxDiff = None
        self.assertEquals(reference, result)

    def test_listing_broken_filter(self):
        reference, result = self.runReplay('_fileset-listing?filter=broken')
        self.maxDiff = None
        self.assertEquals(reference, result)

    def test_listing_filter(self):
        reference, result = self.runReplay('fileset_listing_route', {
            'filter': json.dumps({
                'marv.filter::filter_name::name': {
                    'op': 'substring',
                    'val': '1'
                },
                'marv.filter::filter_md5::md5': {
                    'op': 'startswith',
                    'val': '1'
                },
                'marv.filter::filter_size::size': {
                    'op': '>=',
                    'val': '1'
                },
                'marv.filter::filter_size::size': {
                    'op': '>=',
                    'val': '1G'
                },
                'marv.filter::filter_comment::comment': {
                    'op': 'substring',
                    'val': '1'
                },
                'bagbunker.filter::filter_robot::robot': {
                    'op': 'substring',
                    'val': '1'
                },
                'bagbunker.filter::filter_starttime::num': {
                    'op': '>=',
                    'val': 0
                },
                'bagbunker.filter::filter_endtime_::num': {
                    'op': '<=',
                    'val': 0
                },
                'bagbunker.filter::filter_duration::num': {
                    'op': '>=',
                    'val': 1
                },
                'bagbunker.filter::filter_msgtypes_matching::msgtype': {
                    'op': 'substring',
                    'val': '1'
                },
                'bagbunker.filter::filter_topics_matching::topic': {
                    'op': 'substring',
                    'val': '1'
                }
            })
        })
        self.maxDiff = None
        self.assertEqual(result['rows'], [], 'Filter intended to return empty list')
        self.assertEquals(reference, result)

    def test_summary(self):
        reference, result = self.runReplay('_fileset-summary')
        self.maxDiff = None
        self.assertEquals(reference, result)
