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

from marv import bb, db


@bb.fileset()
class Bag(object):
    starttime = db.Column(db.DateTime(timezone=True), nullable=False)
    endtime = db.Column(db.DateTime(timezone=True), nullable=False)
    duration = db.Column(db.Interval, nullable=False)


class BagMsgType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # XXX: probably only ascii
    name = db.Column(db.String(126), unique=True, index=True, nullable=False)


class BagTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # XXX: probably only ascii
    name = db.Column(db.String(126), unique=True, index=True)


class BagTopics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bag = db.relationship('Bag', uselist=False, backref=db.backref('topics'))
    bag_id = db.Column(db.Integer, db.ForeignKey('bag.id'), nullable=False)
    topic = db.relationship('BagTopic', uselist=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('bag_topic.id'), nullable=False)
    msg_type = db.relationship('BagMsgType', uselist=False)
    msg_type_id = db.Column(db.Integer, db.ForeignKey('bag_msg_type.id'),
                            nullable=False)
    msg_count = db.Column(db.Integer)

    def __repr__(self):
        return '<{}.{} topic="{}" msg_type="{}" msg_count={}>'.format(
            self.__module__, self.__class__.__name__,
            self.topic.name, self.msg_type.name, self.msg_count)
