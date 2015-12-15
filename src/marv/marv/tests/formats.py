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
from collections import OrderedDict
from fnmatch import fnmatch
from marv import bb, db
from ..scanner import FilesetInfo


READER = OrderedDict()
SCANNER = OrderedDict()
PAT1 = '*.fmt1'
PAT2 = '*.fmt2'


@bb.fileset()
class Model1(object):
    content = db.Column(db.String)


@bb.scanner(pattern=PAT1, registry=SCANNER)
def scan_format1(fileinfos):
    """Each file is its own set"""
    for info in fileinfos:
        assert fnmatch(info.filename, PAT1)
        yield FilesetInfo(name=os.path.basename(info.filename),
                          type=Model1, files=(info,), broken=False)


@bb.reader(Model1, registry=READER)
def reader_model1(fileset):
    """A reader receives one fileset at a time"""
    assert fileset.type == 'model1'
    assert fileset.model1 is None
    content = ''
    for file in fileset.files:
        with open(file.path, 'rb') as f:
            content += f.read()
    return Model1(content=content)


@bb.fileset()
class Model2A(object):
    content = db.Column(db.String)


@bb.fileset()
class Model2B(object):
    content = db.Column(db.String)


@bb.scanner(pattern=PAT2, registry=SCANNER)
def scan_format2(fileinfos):
    """Accumulate files into 2 sets of different types"""
    files1 = []
    files2 = []
    for _, _, info in sorted((x.dirpath, x.filename, x) for x in fileinfos):
        assert fnmatch(info.filename, PAT2)
        if int(info.filename[4]) % 2:
            files2.append(info)
        else:
            files1.append(info)
    if files1:
        yield FilesetInfo(name='foo', type=Model2A, files=files1, broken=False)
    if files2:
        yield FilesetInfo(name='bar', type=Model2B, files=files2, broken=False)


@bb.reader(Model2A, registry=READER)
def reader_model2A(fileset):
    """A reader receives one fileset at a time"""
    assert fileset.type == 'model2_a'
    assert fileset.model1 is None
    content = ''
    for file in fileset.files:
        with open(file.path, 'rb') as f:
            content += f.read()
    return Model2A(content=content)


@bb.reader(Model2B, registry=READER)
def reader_model2B(fileset):
    """A reader receives one fileset at a time"""
    assert fileset.type == 'model2_b'
    assert fileset.model1 is None
    content = ''
    for file in fileset.files:
        with open(file.path, 'rb') as f:
            content += f.read()
    return Model2B(content=content)
