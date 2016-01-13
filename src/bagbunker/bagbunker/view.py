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
from datetime import datetime


# @bb.summary()
# @bb.table_widget(title='Bag summary')
# @bb.column('message_count')
# @bb.column('duration', title='Duration (s)')
# def summary_total(filesets):
#     return [{
#         'message_count': db.session
#                            .query(db.func.sum(Bag.message_count))
#                            .select_from(filesets.subquery())
#                            .join(Bag).first()[0],
#         'duration': db.session
#                       .query(db.func.sum(Bag.duration))
#                       .select_from(filesets.subquery())
#                       .join(Bag).first()[0]
#     }]


def dt_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp)


@bb.listing()
@bb.listing_column('starttime', formatter='date')
@bb.listing_column('endtime', formatter='date')
@bb.listing_column('duration (s)', formatter='float')
def listing(fileset):
    bag = fileset.bag
    if not bag:
        return {}
    return {
        # XXX: investigate why isoformat is not standard anymore
        'starttime': bag.starttime.isoformat(),
        'endtime': bag.endtime.isoformat(),
        'duration (s)': bag.duration.total_seconds(),
    }


# --> deepfield_meta.view; should be defined here but deactivated via config
# or meta k/v are declared and can be configured to be displayed in one place
# @bb.detail()
# @bb.table_widget()
# @bb.column('starttime', formatter='date')
# @bb.column('endtime', formatter='date')
# @bb.column('duration (s)')
# def bag_meta(fileset):
#     bag = fileset.bag
#     if not bag:
#         return None
#     return [{
#         'starttime': bag.starttime,
#         'endtime': bag.endtime,
#         'duration (s)': bag.duration.total_seconds(),
#     }]


@bb.detail()
@bb.table_widget(sort='topic')
@bb.column('topic')
@bb.column('type')
@bb.column('message_count')
def bag_topics(fileset):
    bag = fileset.bag
    if not bag:
        return None
    return [{'topic': x.topic.name,
             'type': x.msg_type.name,
             'message_count': x.msg_count}
            for x in bag.topics]
