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

from marv import bb
from marv.model import db, File
from bagbunker.model import Bag
from .metadata import Metadata


@bb.summary()
@bb.table_widget(title='')
@bb.column('fileset_count')
@bb.column('file_count')
@bb.column('total_size', formatter='size')
@bb.column('duration', title='Duration (s)')
def summary(filesets):
    file_count = db.session \
                   .query(File) \
                   .select_from(filesets.subquery()) \
                   .join(File) \
                   .count()
    total_size = int(db.session
                     .query(db.func.sum(File.size))
                     .select_from(filesets.subquery())
                     .join(File)
                     .first()[0])
    durations = db.session \
                  .query(Bag.duration) \
                  .select_from(filesets.subquery()) \
                  .join(Bag) \
                  .all()

    if len(durations):
        duration = sum((x[0] for x in durations[1:]), durations[0][0]).total_seconds()
    else:
        duration = 0
    return [{
        'fileset_count': filesets.count(),
        'file_count': file_count,
        'total_size': total_size,
        'duration': duration,
    }]


@bb.detail()
@bb.table_widget()
@bb.column('robot')
@bb.column('plot')
@bb.column('crop')
@bb.column('bbch-growth')
@bb.column('weeds')
@bb.column('row-spacing')
@bb.column('starttime', formatter='date')
@bb.column('endtime', formatter='date')
@bb.column('duration (s)')
@bb.column('label-file')
@bb.column('additional-files')
def deepfield_metadata(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::metadata')
    meta = Metadata.query.filter(Metadata.jobrun == jobrun).first() \
        if jobrun is not None else None

    bag = fileset.bag
    return [{
        'robot': meta.robot_name if meta else None,
        'plot': meta.plot if meta else None,
        'crop': meta.crop if meta else None,
        'bbch-growth': meta.bbch_growth if meta else None,
        'weeds': [w.name for w in meta.weeds] if meta else None,
        'row-spacing': '%s cm; %s cm' % (meta.row_spacing_inter, meta.row_spacing_intra) if meta else None,
        'starttime': bag.starttime if bag else None,
        'endtime': bag.endtime if bag else None,
        'duration (s)': bag.duration.total_seconds() if bag else None,
        'label-file': meta.label_file if meta else None,
        'additional-files': [f.name for f in meta.additional_files] if meta else None,
    }] if meta or bag else None
