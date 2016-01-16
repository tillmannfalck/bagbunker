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
from marv.filtering import comparisons, compare
from marv.listing import related_field
from .view import dt_from_timestamp


@bb.filter()
@bb.filter_input('num', title='Starttime', operators=comparisons,
                 value_type='date')
def filter_starttime(query, ListingEntry, num):
    val = dt_from_timestamp(int(num.val) / 1000).isoformat()
    return query.filter(compare(ListingEntry.starttime, num.op, val))


@bb.filter()
@bb.filter_input('num', title='Endtime',
                 operators=['<=', '<', '==', '!=', '>', '>='],
                 value_type='date')
def filter_endtime(query, ListingEntry, num):
    val = dt_from_timestamp(int(num.val) / 1000).isoformat()
    return query.filter(compare(ListingEntry.endtime, num.op, val))


@bb.filter()
@bb.filter_input('num', title='Duration', operators=comparisons,
                 value_type='float')
def filter_duration(query, ListingEntry, num):
    return query.filter(compare(ListingEntry.duration, num.op, int(num.val)))


# @bb.filter()
# @bb.filter_input('topics',
#                  title='Topics',
#                  operators=['contains'],
#                  value_type='sublist',
#                  constraints=lambda: sorted(list(
#                      itertools.chain.from_iterable(
#                          db.session.query(BagTopic.name)
#                      )
#                  )))
# def filter4(query, topics):
#     Balias = db.aliased(Bag)
#     return query \
#         .join(Balias) \
#         .join((Topic, Balias.topics)) \
#         .filter(BagTopic.name.in_(topics.val)) \
#         .group_by(Balias.id) \
#         .having(db.func.count(Balias.id) == len(topics.val))


@bb.filter()
@bb.filter_input('msgtype', title='Message type', operators=['substring'])
def filter_msgtypes_matching(query, ListingEntry, msgtype):
    field = related_field('msgtypes')
    return query.filter(ListingEntry.msgtypes.any(field.contains(msgtype.val)))


@bb.filter()
@bb.filter_input('topic', title='Topic', operators=['substring'])
def filter_topics_matching(query, ListingEntry, topic):
    field = related_field('topics')
    return query.filter(ListingEntry.topics.any(field.contains(topic.val)))
