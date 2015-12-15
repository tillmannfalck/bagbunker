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

from marv import db, bb
from bagbunker import bb_bag

__version__ = '0.0.0'


@bb.job_model()
class Trajectory(object):
    timestamp = db.Column(db.Integer)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    qx = db.Column(db.Float)
    qy = db.Column(db.Float)
    qz = db.Column(db.Float)
    qw = db.Column(db.Float)


@bb.job()
@bb.config('pose_logging_interval', default=1)
@bb_bag.messages(topics=('/amcl_pose',))
def job(fileset, messages, pose_logging_interval):
    next_log_time = 0
    log_next_position = 0
    distance_traveled = 0

    for topic, msg, timestamp in messages:
        now = msg.header.stamp.to_sec()
        if log_next_position == 1 or now >= next_log_time:
            log_next_position = 0
            next_log_time = now + pose_logging_interval
            yield Trajectory(timestamp=now,
                             x=msg.pose.pose.position.x,
                             y=msg.pose.pose.position.y,
                             z=msg.pose.pose.position.z,
                             qx=msg.pose.pose.orientation.x,
                             qy=msg.pose.pose.orientation.y,
                             qz=msg.pose.pose.orientation.z,
                             qw=msg.pose.pose.orientation.w)
