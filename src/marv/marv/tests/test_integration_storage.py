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
import hashlib
import os
import shutil
from flask import Flask
from testfixtures import LogCapture
from .. import bb
from ..model import db
from ..storage import Storage
from ..testing import create_tempdir, default_from_self, make_fileset
from .test_scanner import TEST_SCANNER


TEST_READER = dict()


@bb.fileset()
class Foo(object):
    count = db.Column(db.Integer)


@bb.fileset()
class Bar(object):
    count = db.Column(db.Integer)


@bb.reader(Foo, registry=TEST_READER)
def foo_reader(fileset):
    count = 0
    for file in fileset.files:
        with open(file.path) as f:
            count += len(f.read())
    return Foo(count=count)


@bb.reader(Bar, registry=TEST_READER)
def bar_reader(fileset):
    count = 0
    for file in fileset.files:
        with open(file.path) as f:
            count += len(f.read().split('.'))
    return Bar(count=count)


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
        self.storage = Storage.new_storage(reader=TEST_READER, scanner=TEST_SCANNER)

    def tearDown(self):
        self.cleanup()

    @default_from_self
    def test_multiple_formats_multiple_dirs(self, path, storage):
        """Filesets of multiple formats are found in multiple directories"""
        # make filesets in two sibling locations
        path1 = os.path.join(path, 'one')
        path2 = os.path.join(path, 'two')
        os.mkdir(path1)
        os.mkdir(path2)
        make_fileset(path1)
        make_fileset(path2, format='bar')

        # scan both paths using scan_all
        with LogCapture('marv') as log:
            storage.scan_all((path1, path2))
            log.check(('marv.scanner', 'DEBUG', 'Scanning %s' % path1),
                      ('marv.storage', 'INFO',
                       'added new <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path1),
                      ('marv.scanner', 'DEBUG', 'Scanning %s' % path2),
                      ('marv.storage', 'INFO',
                       'added new <Fileset "set0" type="bar" dir="%s"'
                       ' files=3 md5="be8da9c3332394489de53e33c0fdbc63">' % path2))

        self.assertEqual(len(list(storage.filesets)), 2)
        self.assertEqual(len(list(storage.pending_filesets)), 2)

        # rescan finds nothing new
        with LogCapture('marv') as log:
            storage.scan_all((path1, path2))
            log.check(('marv.scanner', 'DEBUG', 'Scanning %s' % path1),
                      ('marv.scanner', 'DEBUG', 'Scanning %s' % path2),)

        with LogCapture('marv') as log:
            storage.read_pending()
            log.check(('marv.storage', 'INFO', 'reading'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path1),
                      ('marv.storage', 'DEBUG', 'read'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path1),
                      ('marv.storage', 'INFO', 'reading'
                       ' <Fileset "set0" type="bar" dir="%s"'
                       ' files=3 md5="be8da9c3332394489de53e33c0fdbc63">' % path2),
                      ('marv.storage', 'DEBUG', 'read'
                       ' <Fileset "set0" type="bar" dir="%s"'
                       ' files=3 md5="be8da9c3332394489de53e33c0fdbc63">' % path2))

        self.assertEqual(len(list(storage.filesets)), 2)
        self.assertEqual(len(list(storage.pending_filesets)), 0)

    @default_from_self
    def test_set_moved(self, path, storage):
        """Update moved set"""
        make_fileset(path)
        storage.scan(path)
        self.assertEqual(len(list(storage.filesets)), 1)
        fileset = storage.filesets[0]
        self.assertEqual(fileset.time_added, fileset.time_updated)

        self.assertEqual(len(list(storage.pending_filesets)), 1)
        storage.read_pending()
        self.assertEqual(len(list(storage.pending_filesets)), 0)

        # move set to subdir
        subdir = os.path.join(path, 'subdir')
        os.mkdir(subdir)
        for x in os.listdir(path):
            shutil.move(os.path.join(path, x), subdir)

        # scan again, fileset is moved and time of update is set
        storage.scan(path)
        self.assertEqual(len(list(storage.filesets)), 1)
        fileset = storage.filesets[0]
        self.assertEqual(fileset.dirpath, subdir)
        self.assertGreater(fileset.time_updated, fileset.time_added)

    @default_from_self
    def test_set_renamed(self, path, storage):
        """Update renamed set"""
        make_fileset(path)
        storage.scan(path)
        self.assertEqual(len(list(storage.filesets)), 1)

        self.assertEqual(len(list(storage.pending_filesets)), 1)
        storage.read_pending()
        self.assertEqual(len(list(storage.pending_filesets)), 0)

        # rename set
        for name in os.listdir(path):
            current = os.path.join(path, name)
            os.rename(current, current.replace('set0', 'renamed'))

        # scan again, fileset is renamed and time of update is set
        storage.scan(path)
        self.assertEqual(len(list(storage.filesets)), 1)
        fileset = storage.filesets[0]
        self.assertEqual(fileset.name, 'renamed')
        self.assertGreater(fileset.time_updated, fileset.time_added)

    @default_from_self
    def test_md5_changed(self, path, storage):
        """Changed fileset md5 results in new fileset superseding old"""
        make_fileset(path)
        storage.scan(path)
        self.assertEqual(len(list(storage.filesets)), 1)

        self.assertEqual(len(list(storage.pending_filesets)), 1)
        storage.read_pending()
        self.assertEqual(len(list(storage.pending_filesets)), 0)

        # change first file and update md5file
        fileset = storage.filesets[0]
        first = fileset.files[0].path
        with open(first, 'wb') as f:
            f.write('foo')
        with open('{}.md5'.format(first), 'wb') as f:
            f.write(hashlib.md5('foo').hexdigest())

        # scan again, new fileset superseds old fileset
        with LogCapture('marv') as log:
            storage.scan(path)
            log.check(('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                      ('marv.storage', 'INFO',
                       '<Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="09eaea0805dcf1e53275dd3466c9a9d2">'
                       ' superseds'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">'
                       % (path, path)))

        filesets = list(storage.filesets)
        self.assertEqual(len(filesets), 2)
        old, new = filesets
        self.assertEqual(old.name, new.name)
        self.assertTrue(old.deleted)
        # self.assertEqual(old.deleted_reason, '__superseded__')
        self.assertEqual(old.deleted_reason, '__supersed')
        self.assertFalse(new.deleted)
        self.assertEqual(len(old.files), 3)
        self.assertEqual(len(new.files), 3)
        self.assertEqual(old.time_added, old.time_updated)
        self.assertEqual(new.time_added, new.time_updated)

        self.assertEqual(len(list(storage.filesets)), 2)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        self.assertEqual(len(list(storage.pending_filesets)), 1)
        self.assertEqual(new, storage.pending_filesets[0])

    @default_from_self
    def test_extend_fileset(self, path, storage):
        """Extended fileset results in new fileset and deleted old"""
        make_fileset(path)
        storage.scan(path)
        self.assertEqual(len(list(storage.filesets)), 1)

        self.assertEqual(len(list(storage.pending_filesets)), 1)
        storage.read_pending()
        self.assertEqual(len(list(storage.pending_filesets)), 0)

        make_fileset(path, parts=4)

        # scan again, new fileset superseds old fileset
        with LogCapture('marv') as log:
            storage.scan(path)
            log.check(('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                      ('marv.storage', 'INFO',
                       '<Fileset "set0" type="foo" dir="%s"'
                       ' files=4 md5="c230765c4dad144e103a7449b29ea180">'
                       ' superseds'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">'
                       % (path, path)))

        filesets = list(storage.filesets)
        self.assertEqual(len(filesets), 2)
        old, new = filesets
        self.assertEqual(old.name, new.name)
        self.assertTrue(old.deleted)
        # self.assertEqual(old.deleted_reason, '__superseded__')
        self.assertEqual(old.deleted_reason, '__supersed')
        self.assertFalse(new.deleted)
        self.assertEqual(len(old.files), 3)
        self.assertEqual(len(new.files), 4)
        self.assertEqual(old.time_added, old.time_updated)
        self.assertEqual(new.time_added, new.time_updated)

        self.assertEqual(len(list(storage.filesets)), 2)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        self.assertEqual(len(list(storage.pending_filesets)), 1)
        self.assertEqual(new, storage.pending_filesets[0])

    @default_from_self
    def test_duplicate_same_set_different_dir(self, path, storage):
        """Duplicates with same name and md5 are skipped"""
        subdir = os.path.join(path, 'subdir')
        os.mkdir(subdir)
        make_fileset(path)
        make_fileset(subdir)

        with LogCapture('marv') as log:
            storage.scan(path)
            log.check(('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                      ('marv.storage', 'INFO', 'added new'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path),
                      ('marv.scanner', 'DEBUG', 'Scanning %s' % subdir),
                      ('marv.storage', 'WARNING', 'skipped duplicate'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">'
                       ' keeping'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">'
                       % (subdir, path)))

        self.assertEqual(len(list(storage.filesets)), 1)

    @default_from_self
    def test_duplicate_same_set_different_name(self, path, storage):
        """Duplicates with different name but same md5 are skipped"""
        make_fileset(path, content_template='file%(file_idx)s.%(format)s')
        make_fileset(path, content_template='file%(file_idx)s.%(format)s', set_idx=1)
        with LogCapture('marv') as log:
            storage.scan(path)
            log.check(('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                      ('marv.storage', 'INFO', 'added new'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="e1307bf746407abcad3987b8f454f5e2">' % path),
                      ('marv.storage', 'WARNING', 'skipped duplicate'
                       ' <Fileset "set1" type="foo" dir="%s"'
                       ' files=3 md5="e1307bf746407abcad3987b8f454f5e2">'
                       ' keeping'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="e1307bf746407abcad3987b8f454f5e2">'
                       % (path, path)))

        self.assertEqual(len(list(storage.filesets)), 1)

    @default_from_self
    def test_duplicate_same_name_different_set(self, path, storage):
        """Duplicates with same name but different md5 are skipped"""
        subdir = os.path.join(path, 'subdir')
        os.mkdir(subdir)
        make_fileset(path, content_template='foo_file%(file_idx)s.%(format)s')
        make_fileset(subdir, content_template='bar_file%(file_idx)s.%(format)s')
        with LogCapture('marv') as log:
            storage.scan(path)
            log.check(('marv.scanner', 'DEBUG', 'Scanning %s' % path),
                      ('marv.storage', 'INFO', 'added new'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="fa5fdfa3e91db83f6f0bcbc01a4257b3">' % path),
                      ('marv.scanner', 'DEBUG', 'Scanning %s' % subdir),
                      ('marv.storage', 'WARNING', 'skipped duplicate'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="1cc962eab33bb3e5e135ca2afaa945bb">'
                       ' keeping'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="fa5fdfa3e91db83f6f0bcbc01a4257b3">'
                       % (subdir, path)))

        self.assertEqual(len(list(storage.filesets)), 1)

    @default_from_self
    def test_deleted_first_file(self, path, storage):
        """First file of a set disappears"""
        make_fileset(path)
        storage.scan(path)
        os.unlink(storage.filesets[0].files[0].path)
        with LogCapture('marv.storage') as log:
            storage.scan(path)
            log.check(('marv.storage', 'WARNING', 'Lost file'
                       ' <File "set0.file0.foo"'
                       ' md5="6cebfe17ca8223e602c4bbff01297d32" size=22>'
                       ' of <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path),)

        self.assertEqual(len(list(storage.filesets)), 1)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        self.assertEqual(len(list(storage.active_intact_filesets)), 0)
        self.assertEqual(len(list(storage.broken_filesets)), 1)
        self.assertTrue(storage.filesets[0].broken)
        self.assertTrue(storage.filesets[0].files[0].missing)

        make_fileset(path)
        with LogCapture('marv.storage') as log:
            storage.scan(path)
            log.check(('marv.storage', 'INFO', 'Found missing file'
                       ' <File "set0.file0.foo"'
                       ' md5="6cebfe17ca8223e602c4bbff01297d32" size=22>'
                       ' of <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path),)
        self.assertEqual(len(list(storage.filesets)), 1)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        self.assertEqual(len(list(storage.active_intact_filesets)), 1)
        self.assertEqual(len(list(storage.broken_filesets)), 0)
        self.assertFalse(storage.filesets[0].broken)
        self.assertFalse(storage.filesets[0].files[0].missing)

    @default_from_self
    def test_deleted_second_file(self, path, storage):
        """Second file of a set disappears"""
        make_fileset(path)
        storage.scan(path)
        os.unlink(storage.filesets[0].files[1].path)
        with LogCapture('marv.storage') as log:
            storage.scan(path)
            log.check(('marv.storage', 'WARNING', 'Lost file'
                       ' <File "set0.file1.foo"'
                       ' md5="d7d0c0e534223916613b8f245d9352fd" size=22>'
                       ' of <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path),)
        self.assertEqual(len(list(storage.filesets)), 1)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        self.assertEqual(len(list(storage.active_intact_filesets)), 0)
        self.assertEqual(len(list(storage.broken_filesets)), 1)
        self.assertTrue(storage.filesets[0].broken)
        self.assertTrue(storage.filesets[0].files[1].missing)

        make_fileset(path)
        with LogCapture('marv.storage') as log:
            storage.scan(path)
            log.check(('marv.storage', 'INFO', 'Found missing file'
                       ' <File "set0.file1.foo"'
                       ' md5="d7d0c0e534223916613b8f245d9352fd" size=22>'
                       ' of <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path),)
        self.assertEqual(len(list(storage.filesets)), 1)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        self.assertEqual(len(list(storage.active_intact_filesets)), 1)
        self.assertEqual(len(list(storage.broken_filesets)), 0)
        self.assertFalse(storage.filesets[0].broken)
        self.assertFalse(storage.filesets[0].files[1].missing)

    @default_from_self
    def test_delete_fileset(self, path, storage):
        """Fileset info flagged deleted"""
        make_fileset(path)
        storage.scan(path)
        self.assertEqual(len(list(storage.filesets)), 1)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        storage.filesets[0].deleted = True
        storage.filesets[0].deleted_reason = 'foo'
        db.session.commit()
        self.assertEqual(len(list(storage.filesets)), 1)
        self.assertEqual(len(list(storage.active_filesets)), 0)
        with LogCapture('marv.storage') as log:
            storage.scan(path)
            log.check(('marv.storage', 'INFO', 'added new'
                       ' <Fileset "set0" type="foo" dir="%s"'
                       ' files=3 md5="03ed01292b64595cf975353d93fb1fdb">' % path),)
        self.assertEqual(len(list(storage.filesets)), 2)
        self.assertEqual(len(list(storage.active_filesets)), 1)
        self.assertEqual(storage.filesets[0].deleted_reason, 'foo')
