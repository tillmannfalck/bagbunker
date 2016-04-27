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

from itertools import product
from collections import defaultdict
from marv import bb
from marv.bb import job_logger as logger
from bagbunker import bb_bag

__version__ = '0.0.6'

# POSITION topics with descending priority: first found will be used.
POSITION_TOPICS = (
    '/sensor/gps/leica1200/fix',
    '/sensor/gps/trimble/fix',
    '/sensor/gps/evk7ppp/fix',
    '/gps/fix',
)
ORIENTATION_TOPICS = (
    '/sensor/imu/xsens_mti/data',
    '/gps/orientation',
)

TOPICS = POSITION_TOPICS + ORIENTATION_TOPICS


def detail_image_view(topic, orient_topic):
    @bb.detail()
    @bb.image_widget(title='Position plot {}, {}'.format(topic, orient_topic))
    def detail_image(fileset):
        jobrun = fileset.get_latest_jobrun('deepfield::gps_track')
        if not jobrun:
            return None

        jobfiles = [x for x in jobrun.jobfiles
                    if x.name.startswith(topic.replace("/", "_"))]

        if not jobfiles:
            return None

        group, name = jobrun.name.split('::')

        jobfile = jobfiles[0]
        return {
            'alt': jobfile.name,
            # XXX: this should be stored on jobfile or we could just
            # return a jobfile instance
            'src': '/'.join(['/marv/jobrun', group, name,
                            str(jobrun.id), jobfile.name]),
        }


# We register a view for each gps topic, but so far the gps job can
# only process one topic.
for topic, orient_topic in product(POSITION_TOPICS, ORIENTATION_TOPICS):
    detail_image_view(topic, orient_topic)


@bb.job()
@bb_bag.messages(topics=TOPICS)
def job(fileset, messages):
    position_topics = [x.topic.name for x in fileset.bag.topics
                       if x.topic.name in POSITION_TOPICS]
    orientation_topics = [x.topic.name for x in fileset.bag.topics
                          if x.topic.name in ORIENTATION_TOPICS]
    if not position_topics:
        logger.debug('no gps topic found')
        return []
    logger.info('starting with {} and {}'.format(position_topics,
                                                 orientation_topics))

    import datetime
    import pyproj
    import matplotlib.dates as md
    import matplotlib.pyplot as plt
    from matplotlib import cm
    import numpy as np

    proj = pyproj.Proj(proj='utm', zone=32, ellps='WGS84')

    class Position(object):
        def __init__(self):
            self.e_offset = 0
            self.n_offset = 0
            self.u_offset = 0
            self.gps = []

        def update(self, msg):
            e, n = proj(msg.longitude, msg.latitude)

            if self.e_offset == 0:
                self.e_offset, self.n_offset, self.u_offset = e, n, msg.altitude

            e, n, u = (e - self.e_offset,
                       n - self.n_offset,
                       msg.altitude - self.u_offset)

            self.gps.append([
                msg.header.stamp.to_sec(),
                msg.latitude,
                msg.longitude,
                msg.altitude,
                e, n, u,
                msg.status.status,
                np.sqrt(msg.position_covariance[0])
            ])

    class Orientation(object):
        def __init__(self):
            self.orientation = []

        def update(self, msg):
            if hasattr(msg, 'yaw') and not np.isnan(msg.yaw):
                self.orientation.append([
                    msg.header.stamp.to_sec(),
                    msg.yaw
                    ])
            elif hasattr(msg, 'orientation') and not np.isnan(msg.orientation.x):
                self.orientation.append([
                    msg.header.stamp.to_sec(),
                    self.yaw_angle(msg.orientation)
                ])

        # calculate imu orientation
        @staticmethod
        def yaw_angle(frame):
            rot = np.zeros((3, 3))

            # consists of time, x, y, z, w
            q1 = frame.x
            q2 = frame.y
            q3 = frame.z
            q4 = frame.w

            rot[0, 0] = 1 - 2 * q2 * q2 - 2 * q3 * q3
            rot[0, 1] = 2 * (q1 * q2 - q3 * q4)
            rot[0, 2] = 2 * (q1 * q3 + q2 * q4)
            rot[1, 0] = 2 * (q1 * q2 + q3 * q4)
            rot[1, 1] = 1 - 2 * q1 * q1 - 2 * q3 * q3
            rot[1, 2] = 2 * (q2 * q3 - q1 * q4)
            rot[2, 0] = 2 * (q1 * q3 - q2 * q4)
            rot[2, 1] = 2 * (q1 * q4 + q2 * q3)
            rot[2, 2] = 1 - 2 * q1 * q1 - 2 * q2 * q2

            vec = np.dot(rot, [1, 0, 0])

            # calculate the angle
            return np.arctan2(vec[1], vec[0])

    positionMap = {position_topic: Position() for position_topic in position_topics}
    orientationMap = {orientation_topic: Orientation()
                      for orientation_topic in orientation_topics}
    erroneous_msg_count = defaultdict(int)

    for topic, msg, timestamp in messages:
        if topic in position_topics:
            # skip erroneous messages
            if np.isnan(msg.longitude) or \
               np.isnan(msg.latitude) or \
               np.isnan(msg.altitude):
                erroneous_msg_count[topic] += 1
                continue

            if hasattr(msg, 'status'):
                positionMap[topic].update(msg)
            else:
                raise Exception('Invalid position topic')
        elif topic in orientation_topics:
            orientationMap[topic].update(msg)

    if erroneous_msg_count:
        logger.warn('Skipped erroneous GNSS messages %r', erroneous_msg_count.items())

    for position_topic, orientation_topic in product(
            position_topics, orientation_topics
    ):
        gps = np.array(positionMap[position_topic].gps)

        if not len(gps):
            logger.error('Aborting due to missing gps messages on topic %s',
                         position_topic)
            continue

        if orientationMap[orientation_topic].orientation:
            orientation = np.array(orientationMap[orientation_topic].orientation)
        else:
            logger.warn('No orientation messages on topic %s', orientation_topic)

        # plotting
        fig = plt.figure()
        fig.subplots_adjust(wspace=0.3)

        ax1 = fig.add_subplot(1, 3, 1)  # e-n plot
        ax2 = fig.add_subplot(2, 3, 2)  # orientation plot
        ax3 = fig.add_subplot(2, 3, 3)  # e-time plot
        ax4 = fig.add_subplot(2, 3, 5)  # up plot
        ax5 = fig.add_subplot(2, 3, 6)  # n-time plot

        # masking for finite values
        gps = gps[np.isfinite(gps[:, 1])]

        # precompute plot vars
        c = cm.prism(gps[:, 7]/2)

        ax1.scatter(gps[:, 4], gps[:, 5], c=c, edgecolor='none', s=3,
                    label="green: RTK\nyellow: DGPS\nred: Single")

        xfmt = md.DateFormatter('%H:%M:%S')
        ax2.xaxis.set_major_formatter(xfmt)
        ax3.xaxis.set_major_formatter(xfmt)
        ax4.xaxis.set_major_formatter(xfmt)
        ax5.xaxis.set_major_formatter(xfmt)

        if orientationMap[orientation_topic].orientation:
            ax2.plot([datetime.datetime.fromtimestamp(timestamp)
                      for timestamp in orientation[:, 0]], orientation[:, 1])

        ax3.plot([datetime.datetime.fromtimestamp(timestamp)
                  for timestamp in gps[:, 0]], gps[:, 4])
        ax4.plot([datetime.datetime.fromtimestamp(timestamp)
                  for timestamp in gps[:, 0]], gps[:, 6])
        ax5.plot([datetime.datetime.fromtimestamp(timestamp)
                  for timestamp in gps[:, 0]], gps[:, 5])

        fig.autofmt_xdate()

        # add the legends
        ax1.legend(loc="best")

        ax1.set_ylabel('GNSS northing [m]')
        ax1.set_xlabel('GNSS easting [m]')
        ax2.set_ylabel('Heading over time [rad]')
        ax3.set_ylabel('GNSS easting over time [m]')
        ax4.set_ylabel('GNSS height over time [m]')
        ax5.set_ylabel('GNSS northing over time [m]')

        fig.set_size_inches(16, 9)
        path = bb.make_job_file(position_topic.replace("/", "_")+'.jpg')

        try:
            fig.savefig(path)
        except:
            logger.warn(gps[:, 4])
            logger.warn(gps[:, 5])
            logger.warn(gps[:, 6])
            raise
    return []
