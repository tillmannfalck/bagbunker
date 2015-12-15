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
import unittest
from collections import defaultdict
from functools import partial
from testfixtures import LogCapture
from .. import bb
from ..scanner import FilesetInfo
from ..scanner import detect_filesets as _detect_filesets
from ..scanner import scan as _scan
from ..testing import create_tempdir, make_fileset


TEST_SCANNER = dict()


def detect_filesets(basedir):
    scanners = TEST_SCANNER.values()
    return _detect_filesets(basedir, scanners)


scan = partial(_scan, scanner=TEST_SCANNER)


def _make_test_scanner(extension):
    @bb.scanner(name='scanner_{}'.format(extension),
                pattern='*.{}'.format(extension), registry=TEST_SCANNER)
    def scanner(fileinfos):
        sets = defaultdict(list)
        for fileinfo in fileinfos:
            setname, idx, format = fileinfo.name.split('.')
            idx = int(idx.lstrip('file'))
            assert format == extension
            sets[fileinfo.dirpath, setname].append((idx, fileinfo))

        for (dirpath, name), indexed_files in sorted(sets.items()):
            indexed_files.sort()
            yield FilesetInfo(name=name, dirpath=dirpath,
                              type=extension, indexed_files=indexed_files)

    return scanner


_make_test_scanner('foo')
_make_test_scanner('bar')


class TestCase(unittest.TestCase):
    """
    - A set's name is unique

    - All parts of a set reside within one directory

    - Two different files cannot have the same content -
      they have the same md5 and are treated as duplicates.
    """
    def setUp(self):
        self.path, self.cleanup = create_tempdir()

    def tearDown(self):
        self.cleanup()

    def test_detect_skip_hidden(self):
        """Files starting with a '.' are hidden from the scanner"""
        path = self.path
        make_fileset(path)
        make_fileset(path, prefix='.', set_idx=1)
        filesets = list(detect_filesets(path))
        self.assertEqual(len(filesets), 1)

    def test_detect_multiple_formats(self):
        """Detect sets of two different formats"""
        path = self.path
        make_fileset(path)
        make_fileset(path, format='bar')
        filesets = list(detect_filesets(path))
        self.assertEqual(set([x.type for x in filesets]), set(['foo', 'bar']))

    def test_duplicates_in_scan_are_fine(self):
        """Scanner does not care about duplicate filesets, the database does"""
        path = self.path
        subdir = os.path.join(self.path, 'subdir')
        os.mkdir(subdir)
        make_fileset(path)
        make_fileset(subdir)
        filesets = list(detect_filesets(path))
        self.assertEqual(len(filesets), 2)

    def test_scan_empty(self):
        """Filesets of three files containing empty files: 011, 101, 110"""
        path = self.path
        for i in range(3):
            make_fileset(path, set_idx=i, empty_idx=i)
        with LogCapture('marv') as log:
            filesets = list(scan(path))
            log.check(
                ('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                ('marv.scanner', 'WARNING',
                 "('EmptyFile', '%s', 'set0.file0.foo')" % path),
                ('marv.scanner', 'WARNING',
                 "('EmptyFile', '%s', 'set1.file1.foo')" % path),
                ('marv.scanner', 'WARNING',
                 "('EmptyFile', '%s', 'set2.file2.foo')" % path),
            )
        self.assertEqual(len(filesets), 0)

    def test_scan_missing(self):
        """Filesets of three files with missing file: 011, 101, 110"""
        path = self.path
        for i in range(3):
            make_fileset(path, set_idx=i, missing_idx=i)
        with LogCapture('marv') as log:
            filesets = list(scan(path))
            log.check(
                ('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                ('marv.scanner', 'WARNING',
                 "('MissingFile', '%s', 'set0', 1)" % path),
                ('marv.scanner', 'WARNING',
                 "('MissingFile', '%s', 'set1', 1)" % path),
            )
        # We have no way to detect that 110 is missing the last file
        self.assertEqual(len(filesets), 1)
        self.assertEqual(len(filesets[0].files), 2)

    def test_scan_missing_md5(self):
        """Filesets of three files with missing md5s: 011, 101, 110"""
        path = self.path
        for i in range(3):
            make_fileset(self.path, set_idx=i, missing_md5_idx=i)
        with LogCapture('marv') as log:
            filesets = list(scan(path))
            log.check(
                ('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                ('marv.scanner', 'WARNING',
                 "('MissingMD5', '%s', 'set0.file0.foo')" % path),
                ('marv.scanner', 'WARNING',
                 "('MissingMD5', '%s', 'set1.file1.foo')" % path),
                ('marv.scanner', 'WARNING',
                 "('MissingMD5', '%s', 'set2.file2.foo')" % path),
            )
        self.assertEqual(len(filesets), 0)
