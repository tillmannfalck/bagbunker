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

import hashlib
import os
from collections import namedtuple
from datetime import datetime
from fnmatch import fnmatch
from logging import getLogger
from .model import File, Fileset
from ._utils import multiplex
from .widgeting import make_register, WidgetBase


class Scanner(WidgetBase):
    def __init__(self, pattern, **kw):
        super(Scanner, self).__init__(**kw)
        self.pattern = pattern

    def __call__(self, fileinfos):
        filtered = (x for x in fileinfos
                    if fnmatch(os.path.join(x.dirpath, x.name), self.pattern))
        return self.callback(filtered)


SCANNER = dict()
scanner = make_register('scanner', namespace='', registry=SCANNER, cls=Scanner)

FileInfo = namedtuple('FileInfo', ('dirpath', 'name'))
FilesetInfo = namedtuple('FilesetInfo', ('type', 'dirpath', 'name', 'indexed_files'))


class BrokenFileset(Exception):
    def __init__(self, *args, **kw):
        super(BrokenFileset, self).__init__(self.__class__.__name__, *args, **kw)


class MissingFile(BrokenFileset):
    pass


class MissingMD5(BrokenFileset):
    pass


class EmptyFile(BrokenFileset):
    pass


class UnreadableFile(BrokenFileset):
    pass


class MalformattedMD5(BrokenFileset):
    pass


def detect_filesets(basedir, scanners):
    """Walk basedir using scanners to detect filesets, return filesetinfos"""
    logger = getLogger(__name__)
    assert os.path.isdir(basedir)
    assert len(scanners) > 0
    for dirpath, subdirs, filenames in os.walk(basedir):
        logger.debug('Scanning %s', dirpath)
        fileinfos = (FileInfo(dirpath, filename)
                     for filename in filenames
                     if filename[0] != '.' and     # skip hidden files
                     filename[-4:] != '.md5')      # skip md5 files
        for filesetinfo in list(multiplex(fileinfos, scanners, dont_catch=True)):
            yield filesetinfo


def make_file(fileinfo):
    """Make File model from FileInfo"""
    path = os.path.join(fileinfo.dirpath, fileinfo.name)

    if not os.access(path, os.R_OK):
        raise UnreadableFile(fileinfo.dirpath, fileinfo.name)

    md5file = '{}.md5'.format(path)
    try:
        with open(md5file, 'rb') as f:
            md5str = f.readline()
        md5 = md5str[:32]

        if md5str[32:].strip() != fileinfo.name:
            raise MalformattedMD5(fileinfo.dirpath, fileinfo.name)
    except IOError:
        raise MissingMD5(fileinfo.dirpath, fileinfo.name)

    stat = os.stat(path)
    size = stat.st_size
    if size == 0:
        raise EmptyFile(fileinfo.dirpath, fileinfo.name)

    return File(name=fileinfo.name, md5=md5, size=size)


def make_fileset(filesetinfo):
    """Make Fileset model from FilesetInfo"""
    files = []
    md5 = hashlib.md5()
    for idx, fileinfo in filesetinfo.indexed_files:
        file = make_file(fileinfo)
        files.append(file)
        md5.update(file.md5)

    missing_files = 1 + idx - len(files)
    if missing_files:
        dirpath = filesetinfo.indexed_files[0][1].dirpath
        raise MissingFile(dirpath, filesetinfo.name, missing_files)

    now = datetime.utcnow()
    return Fileset(name=filesetinfo.name, md5=md5.hexdigest(),
                   dirpath=filesetinfo.dirpath, type=filesetinfo.type,
                   files=files, time_added=now, time_updated=now)


def scan(basedir, scanner=SCANNER):
    """Scan basedir, return Fileset models, log warning for broken sets"""
    logger = getLogger(__name__)
    scanners = scanner.values()
    for filesetinfo in detect_filesets(basedir, scanners):
        try:
            fileset = make_fileset(filesetinfo)
        except BrokenFileset as e:
            logger.warn(e)
            continue

        yield fileset
