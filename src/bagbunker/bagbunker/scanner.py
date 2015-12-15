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

import collections
import re
from marv import bb
from marv.scanner import FilesetInfo


@bb.scanner(pattern='*.bag')
def scanner(fileinfos):
    fileset_re = re.compile('(.*?)(?:_(\d+))?\.bag$')
    setfiles = collections.defaultdict(list)
    for fileinfo in fileinfos:
        basename, idx = fileset_re.match(fileinfo.name).groups()
        if idx is None:
            yield FilesetInfo(name=basename, dirpath=fileinfo.dirpath,
                              type='bag', indexed_files=((0, fileinfo),))
            continue
        setfiles[fileinfo.dirpath].append((basename, int(idx), fileinfo))

    for dirpath, dirfiles in sorted(setfiles.items()):
        indexed_files = []
        prev_idx = None
        sets = []
        for basename, idx, fileinfo in sorted(dirfiles, reverse=True):
            if prev_idx is not None and idx != prev_idx - 1:
                # broken set, discard files
                indexed_files = []
                prev_idx = None

            indexed_files.insert(0, (idx, fileinfo))

            if idx == 0:
                sets.insert(0, FilesetInfo(name=basename, dirpath=fileinfo.dirpath,
                                           type='bag', indexed_files=indexed_files))
                indexed_files = []
                prev_idx = None
            else:
                prev_idx = idx

        # return sets in alphabetical order
        for set in sets:
            yield set
