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
from functools import partial
from marv.scanner import detect_filesets as _detect_filesets
from marv.scanner import scan as _scan
from marv.testing import create_tempdir, default_from_self, ls, make_fileset
from ..scanner import scanner


TEST_SCANNER = {'bag': scanner}


def detect_filesets(basedir):
    scanners = TEST_SCANNER.values()
    return _detect_filesets(basedir, scanners)


make_bagset = partial(make_fileset, format='bag',
                      template='set%(set_idx)s.file_%(file_idx)s.%(format)s')
scan = partial(_scan, scanner=TEST_SCANNER)


class TestCase(unittest.TestCase):
    def setUp(self):
        self.path, self.cleanup = create_tempdir()

    def tearDown(self):
        self.cleanup()

    @default_from_self
    def test_scan_missing(self, path):
        for i in range(3):
            make_bagset(path, set_idx=i, missing_idx=2-i)

        files = ls(path)
        self.assertEqual(files, ['set0.file_0.bag',
                                 'set0.file_0.bag.md5',
                                 'set0.file_1.bag',
                                 'set0.file_1.bag.md5',
                                 'set1.file_0.bag',
                                 'set1.file_0.bag.md5',
                                 'set1.file_2.bag',
                                 'set1.file_2.bag.md5',
                                 'set2.file_1.bag',
                                 'set2.file_1.bag.md5',
                                 'set2.file_2.bag',
                                 'set2.file_2.bag.md5'])

        filesets = list(scan(path))
        self.assertEqual(len(filesets), 2)
        self.assertEqual(len(filesets[0].files), 2)
        self.assertEqual(len(filesets[1].files), 1)
