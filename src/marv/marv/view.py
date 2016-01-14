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

import json
from . import bb
from .model import db


def fileset_size(fileset):
    return sum([f.size for f in fileset.files])


# @bb.summary()
# @bb.table_widget(title='Storage summary')
# @bb.column('fileset_count')
# @bb.column('file_count')
# @bb.column('total_size', formatter='size')
# def summary(filesets):
#     return [{
#         'fileset_count': filesets.count(),
#         'file_count': db.session
#                         .query(File)
#                         .select_from(filesets.subquery())
#                         .join(File)
#                         .count(),
#         'total_size': db.session
#                         .query(db.func.sum(File.size))
#                         .select_from(filesets.subquery())
#                         .join(File).first()[0],
#     }]


@bb.listing()
@bb.listing_column('name', formatter='route', json=True)
@bb.listing_column('md5', title='Abbr. MD5')
@bb.listing_column('size', formatter='size', type=db.Integer)
@bb.listing_column('file_count', title='# files', type=db.Integer)
@bb.listing_column('status', formatter='icon', list=True, json=True)
@bb.listing_column('job_count', title='# jobs', type=db.Integer)
@bb.listing_column('comment_count', title='# comments', type=db.Integer)
@bb.listing_column('tags', formatter='pill', list=True, json=True)
@bb.listing_column('tags_relation', hidden=True, relation=True)
# @bb.column('downloads', title="Download Parts", formatter='link', list=True)
def base_listing(fileset):
    md5 = fileset.md5
    tags = fileset.tags
    # files = fileset.files
    size = fileset_size(fileset)
    status = []
    if any((f.missing for f in fileset.files)):
        status.append({
            'icon': 'hdd',
            'title': 'A file is missing',
            'classes': 'text-danger',
        })
    if fileset.time_read is None:
        status.append({
            'icon': 'time',
            'title': 'This fileset has not yet been processed',
            'classes': 'text-info',
        })
    elif not fileset.read_succeeded:
        status.append({
            'icon': 'fire',
            'title': 'Read error: {}'.format(fileset.read_error),
            'classes': 'text-danger',
        })
    failed_job_names = fileset.failed_job_names
    if failed_job_names:
        status.append({
            'icon': 'fire',
            'title': 'Failed jobs: {}'.format(', '.join(failed_job_names)),
            'classes': 'text-danger',
        })
    return {
        'name': json.dumps({'route': 'bagbunker.detail', 'id': md5, 'title': fileset.name}),
        'md5': md5[:7],
        'size': size,
        'tags': json.dumps(sorted([t.label for t in tags])),
        'tags_relation': [t.label for t in tags],
        'status': json.dumps(status),
        'file_count': len(fileset.files),
        'job_count': len(fileset.jobruns),
        'comment_count': len(fileset.comments),
        # 'downloads': [
        #     {'href': '/marv/download/{}'.format(md5),
        #      'title': md5[:7]}
        #     for i, x in enumerate(fileset.files.with_entities(File.md5).all())
        #     for md5 in x
        # ]
    }


@bb.detail()
@bb.table_widget(title='Fileset Meta')
@bb.column('name')
@bb.column('md5')
@bb.column('size', formatter='size')
@bb.column('file_count', title='# files')
def fileset_meta(fileset):
    size = fileset_size(fileset)
    return [{
        'name': fileset.name,
        'md5': fileset.md5,
        'size': size,
        'file_count': len(fileset.files),
    }]


@bb.detail(state='collapsed')
@bb.table_widget(title='File Meta')
@bb.column('name', formatter='link')
@bb.column('status', formatter='icon', list=True)
@bb.column('md5', title='MD5')
@bb.column('size', formatter='size')
def files_detail(fileset):
    return [{
        'name': {'href': '/marv/download/{}'.format(file.md5),
                 'title': file.name, 'target': '_blank'},
        'status': [{
            'icon': 'hdd',
            'title': 'This file is missing',
            'classes': 'text-danger',
        }] if file.missing else [],
        'md5': file.md5,
        'size': file.size,
    } for file in fileset.files]


@bb.detail()
@bb.table_widget()
@bb.column('status', formatter='icon')
@bb.column('job')
def failed_jobs(fileset):
    if fileset.failed_job_names:
        return [{'status': {'icon': 'fire',
                            'title': 'failed',
                            'classes': 'text-danger'},
                 'job': x} for x in fileset.failed_job_names]
