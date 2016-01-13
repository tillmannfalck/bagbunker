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
from marv import bb, db
from marv.bb import job_logger as logger
from marv.model import Fileset, Jobrun
from bagbunker import bb_bag


__version__ = '0.0.1'


@bb.job_model()
class Metadata(object):
    robot_name = db.Column(db.String(42), nullable=False)
    use_case = db.Column(db.String(126), nullable=False)


@bb.job()
@bb_bag.messages(topics=())
def job(fileset, messages):
    if not fileset.bag:
        return
    path = fileset.dirpath.split(os.sep)
    robot_name = path[3] if len(path) > 3 else 'unknown'
    use_case = path[6] if len(path) > 6 else 'unknown'
    logger.info('robot_name=%s, use_case=%s', robot_name, use_case)
    yield Metadata(robot_name=robot_name, use_case=use_case)


@bb.filter()
@bb.filter_input('robot', operators=['substring'])
def filter_robot(query, robot):
    # XXX: Currently also matches on previous values
    q = db.session \
        .query(Jobrun.fileset_id, db.func.max(Jobrun.id)) \
        .filter(Jobrun.name == 'deepfield::metadata') \
        .group_by(Jobrun.fileset_id) \
        .join(Metadata) \
        .filter(Metadata.robot_name.like('%{}%'.format(robot.val))) \
        .subquery()
    return query.join(q, Fileset.id == q.c.fileset_id)


@bb.filter()
@bb.filter_input('use_case', operators=['substring'])
def filter_use_case(query, use_case):
    # XXX: Currently also matches on previous values
    q = db.session \
        .query(Jobrun.fileset_id, db.func.max(Jobrun.id)) \
        .filter(Jobrun.name == 'deepfield::metadata') \
        .group_by(Jobrun.fileset_id) \
        .join(Metadata) \
        .filter(Metadata.use_case.like('%{}%'.format(use_case.val))) \
        .subquery()
    return query.join(q, Fileset.id == q.c.fileset_id)


@bb.listing()
@bb.listing_column('robot')
@bb.listing_column('use_case')
def listing(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::metadata')
    if jobrun is None:
        return {}

    meta = Metadata.query.filter(Metadata.jobrun == jobrun).first()
    if meta is None:
        return {}
    return {
        'robot': meta.robot_name,
        'use_case': meta.use_case,
    }
