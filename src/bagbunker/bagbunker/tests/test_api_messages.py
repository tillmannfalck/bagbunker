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

import cPickle as pickle
from marv.storage import Storage
from marv.testing import FlaskTestCase, default_from_self
from bagbunker.reader import MessageStreamClient
from pkg_resources import resource_filename
from werkzeug.datastructures import Headers


BAG_DIR = resource_filename(__name__, 'bags')
MD5 = 'cf72dca53687072b2f6f70837eed4c43'


class TestCase(FlaskTestCase):
    def setUp(self):
        # XXX: Would be nice to scan and read only once
        storage = self.storage = Storage.new_storage()
        storage.scan(BAG_DIR)
        storage.read_pending()

    def tearDown(self):
        pass

    @default_from_self
    def test_pick_mimetype(self, client):
        # pick first known, honoring quality
        resp = client.get('/api/messages/{}'.format(MD5), headers=Headers([
            ('Accept',
             'foo/foo;q=1.2,application/x-ros-bag-msgs;q=0.5,foo/bar')]))
        self.assert200(resp)
        self.assertEqual(resp.headers['Content-type'], 'foo/bar')

    @default_from_self
    def test_no_valid_mimetype(self, client):
        # no valid mimetype
        resp = client.get('/api/messages/{}'.format(MD5), headers=Headers([
            ('Accept', 'foo/foo')]))
        self.assert400(resp)

    @default_from_self
    def test_all(self, client):
        # default handler
        resp = client.get('/api/messages/{}'.format(MD5))
        self.assert200(resp)
        self.assertEqual(resp.headers['Content-type'], 'application/x-ros-bag-msgs')
        msc = MessageStreamClient(chunks=iter([resp.data]))
        self.assertEqual(msc.name, 'test_2015-02-05-12-59-06')
        self.assertEqual(msc.topics,
                         {u'/chatter': (2, u'std_msgs/String',
                                        '992ce8a1687cec8c8bd883ec73ca41d1'),
                          u'/rosout': (1, u'rosgraph_msgs/Log',
                                       'acffd30cd6b6de30f120938c17c593fb'),
                          u'/rosout_agg': (0, u'rosgraph_msgs/Log',
                                           'acffd30cd6b6de30f120938c17c593fb')})
        self.assertEqual(len(list(msc.messages)), 29)

    @default_from_self
    def test_one_topic(self, client):
        resp = client.get('/api/messages/{}?topic=/chatter'.format(MD5))
        self.assert200(resp)
        msc = MessageStreamClient(chunks=iter([resp.data]))
        self.assertEqual(msc.topics,
                         {u'/chatter': (2, u'std_msgs/String',
                                        '992ce8a1687cec8c8bd883ec73ca41d1')})
        self.assertEqual(len(list(msc.messages)), 8)

    @default_from_self
    def test_multiple_topic(self, client):
        resp = client.get('/api/messages/{}?topic=/chatter&topic=/rosout'.format(MD5))
        self.assert200(resp)
        msc = MessageStreamClient(chunks=iter([resp.data]))
        self.assertEqual(msc.topics,
                         {u'/chatter': (2, u'std_msgs/String',
                                        '992ce8a1687cec8c8bd883ec73ca41d1'),
                          u'/rosout': (1, u'rosgraph_msgs/Log',
                                       'acffd30cd6b6de30f120938c17c593fb')})
        self.assertEqual(len(list(msc.messages)), 20)

    # @default_from_self
    # def test_msg_type(self, client):
    #     resp = client.get('/api/messages/{}?msg_type=std_msgs/String'.format(MD5))
    #     self.assert200(resp)
    #     topics = pickle.loads(resp.data)
    #     self.assertEqual(topics, {u'/chatter': (2, u'std_msgs/String')})
