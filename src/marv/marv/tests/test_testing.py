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

import unittest
from ..testing import create_tempdir, ls, make_fileset


class TestCase(unittest.TestCase):
    def setUp(self):
        self.path, self.cleanup = create_tempdir()

    def tearDown(self):
        self.cleanup()

    def test_make_fileset(self):
        path = self.path
        make_fileset(path)
        files = ls(path)
        self.assertEqual(files, ['set0.file0.foo',
                                 'set0.file0.foo.md5',
                                 'set0.file1.foo',
                                 'set0.file1.foo.md5',
                                 'set0.file2.foo',
                                 'set0.file2.foo.md5'])

    def test_make_broken_fileset(self):
        path = self.path
        make_fileset(path, empty_idx=0, missing_idx=1, missing_md5_idx=2)
        files = ls(path)
        self.assertEqual(files, ['set0.file0.foo',
                                 'set0.file0.foo.md5',
                                 'set0.file2.foo'])
