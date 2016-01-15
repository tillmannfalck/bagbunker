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

from itertools import chain
from . import bb
from .filtering import COMPARISON_OPS, compare
from .listing import related_field
from .model import db, Tag


@bb.filter()
@bb.filter_input('name', operators=['substring'])
def filter_name(query, ListingEntry, name):
    return query.filter(ListingEntry.name.like('%'+name.val+'%'))


@bb.filter()
@bb.filter_input('md5', title='MD5', operators=['startswith'])
def filter_md5(query, ListingEntry, md5):
    return query.filter(ListingEntry.md5.like(md5.val+'%'))


@bb.filter()
@bb.filter_input('size', operators=COMPARISON_OPS, value_type='filesize')
def filter_size(query, ListingEntry, size):
    return query.filter(compare(ListingEntry.size, size.op, size.val))


@bb.filter()
@bb.filter_input('comment', title='Comment', operators=['substring'])
def filter_comment(query, ListingEntry, comment):
    field = related_field('comments_relation')
    return query \
        .filter(ListingEntry.comments_relation.any(field.contains(comment.val)))


@bb.filter()
@bb.filter_input('tags',
                 title='Tag',
                 operators=['contains'],
                 value_type='sublist',
                 constraints=lambda: sorted(list(
                     chain.from_iterable(db.session.query(Tag.label)))))
def filter_tag(query, ListingEntry, tags):
    field = related_field('tags_relation')
    for val in tags.val:
        query = query.filter(ListingEntry.tags_relation.any(field == val))
    return query
