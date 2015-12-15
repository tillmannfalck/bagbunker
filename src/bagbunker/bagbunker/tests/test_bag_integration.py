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

import flask_testing
import os
from datetime import timedelta
from flask import Flask
from pkg_resources import resource_filename
from marv.model import db, Fileset, File
from marv.storage import Storage
from marv.testing import create_tempdir, default_from_self
from ..model import Bag, BagTopic, BagTopics


BAGS = resource_filename(__name__, 'bags')


class TestCase(flask_testing.TestCase):
    SQLALCHEMY_ECHO = bool(os.environ.get('SQLALCHEMY_ECHO', False))
    TESTING = True

    def create_app(self):
        app = Flask(__name__)
        app.config.from_object(self)
        db.init_app(app)
        return app

    def setUp(self):
        db.create_all()
        self.path, self.cleanup = create_tempdir()
        self.storage = Storage.new_storage()

    def tearDown(self):
        self.cleanup()

    @default_from_self
    def test_integration(self, storage):
        storage.scan(BAGS)

        filesets = Fileset.query.all()
        files = File.query.all()

        self.assertEquals(len(filesets), 3)
        self.assertEquals(len(files), 8)
        self.assertEquals(len(filesets[0].files), 1)
        self.assertEquals(len(filesets[1].files), 1)
        self.assertEquals(len(filesets[2].files), 6)
        self.assertTrue(all((x.type == 'bag') for x in filesets)),

        self.assertEqual(len(list(storage.pending_filesets)), 3)
        storage.read_pending()
        self.assertEqual(len(list(storage.pending_filesets)), 0)
        bags = Bag.query.all()
        self.assertEqual(len(bags), 3)

        fileset = filesets[2]
        self.assertEqual(fileset.name, 'test_2015-02-05-12-59-06')
        self.assertEqual(fileset.bag.duration, timedelta(0, 9, 463955))
        self.assertEqual(len(list(fileset.bag.topics)), 3)
        rosout_agg = BagTopics.query.filter(BagTopics.bag == fileset.bag)\
                                    .join(BagTopic)\
                                    .filter(BagTopic.name == '/rosout_agg')\
                                    .first()
        self.assertEqual(rosout_agg.msg_type.name, 'rosgraph_msgs/Log')
        self.assertEqual(rosout_agg.msg_count, 104)
