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
from marv.bb import job_logger as logger
from marv.model import Jobrun
from bagbunker import bb_bag

__version__ = '0.0.6'

# GPS topics with descending priority: first found will be used.
GPS_TOPICS = (
    '/sensor/gps/leica1200/fix',
    '/sensor/gps/trimble/fix',
    '/sensor/gps/evk7ppp/fix',
)
IMU_TOPIC = '/sensor/imu/xsens_mti/data'
TOPICS = GPS_TOPICS + (IMU_TOPIC,)


def detail_image_view(topic):
    @bb.detail()
    @bb.image_widget(title='GPS plot {}, {}'.format(topic, IMU_TOPIC))
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
for topic in GPS_TOPICS:
    detail_image_view(topic)


@bb.job()
@bb_bag.messages(topics=TOPICS)
def job(fileset, messages):
    gps_topics = [x.topic.name for x in fileset.bag.topics
                  if x.topic.name in GPS_TOPICS]
    if not gps_topics:
        logger.debug('no gps topic found')
        return []
    for gps_topic in gps_topics:
        logger.info('starting with {} and {}'.format(gps_topic, IMU_TOPIC))

    import datetime
    import pyproj
    import matplotlib.pyplot as plt
    from matplotlib import cm, dates
    import numpy as np

    def plot_convert_time(timestamps):
        dts = map(lambda e: datetime.datetime.fromtimestamp(e),
                  timestamps.astype(int))
        return dates.date2num(dts)

    proj = pyproj.Proj(proj='utm', zone=32, ellps='WGS84')

    class GPS(object):
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

    class IMU(object):
        def __init__(self):
            self.orientation = []

        def update(self, msg):
            self.orientation.append([
                msg.header.stamp.to_sec(),
                msg.orientation.x,
                msg.orientation.y,
                msg.orientation.z,
                msg.orientation.w
            ])

    gpsMap = dict([(gps_topic, GPS()) for gps_topic in gps_topics])
    imu = IMU()
    erroneous_msg_count = 0

    for topic, msg, timestamp in messages:
        if topic in gps_topics:
            # skip erroneous messages
            if np.isnan(msg.longitude) or \
               np.isnan(msg.latitude) or \
               np.isnan(msg.altitude):
                erroneous_msg_count += 1
                continue

            if hasattr(msg, 'status'):
                gpsMap[topic].update(msg)
            else:
                raise Exception('Invalid GPS topic')
        elif topic == IMU_TOPIC:
            imu.update(msg)

    if erroneous_msg_count:
        logger.warn('Skipped %s erroneous gps messages on topic %s',
                    erroneous_msg_count, gps_topic)

    # calculate imu orientation
    def yaw_angle(frame):
        rot = np.zeros((3, 3))

        # consists of time, x, y, z, w
        q1 = frame[1]
        q2 = frame[2]
        q3 = frame[3]
        q4 = frame[4]

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

    for gps_topic in gps_topics:
        gps = np.array(gpsMap[gps_topic].gps)

        if not len(gps):
            logger.error('Aborting due to missing gps messages on topic %s', gps_topic)
            continue

        if imu.orientation:
            orientation = np.array(imu.orientation)
        else:
            logger.warn('No imu messages on topic %s', IMU_TOPIC)
            continue

        # plotting
        fig = plt.figure()
        fig.subplots_adjust(wspace=0.3)

        ax1 = fig.add_subplot(1, 3, 1)  # e-n plot
        ax2 = fig.add_subplot(2, 3, 2)  # imu plot
        ax3 = fig.add_subplot(2, 3, 3)  # e-time plot
        ax4 = fig.add_subplot(2, 3, 5)  # up plot
        ax5 = fig.add_subplot(2, 3, 6)  # n-time plot

        # masking for finite values
        gps = gps[np.isfinite(gps[:, 1])]

        # timeseries for x-axis
        timeseries = plot_convert_time(gps[:, 0])

        if imu.orientation:
            timeseries_yaw = plot_convert_time(orientation[:, 0])

            imu_yaw = map(yaw_angle, orientation)

        # precompute plot vars
        c = cm.prism(gps[:, 7]/2)

        ax1.scatter(gps[:, 4], gps[:, 5], c=c, edgecolor='none', s=3,
                    label="green: RTK\nyellow: DGPS\nred: Single")

        if imu.orientation:
            ax2.scatter(timeseries_yaw, imu_yaw, edgecolor='none', s=3)
            ax2.set_xlim([timeseries_yaw.min(), timeseries_yaw.max()])
            ax2.xaxis.set_major_formatter(dates.DateFormatter('%H:%M:%S'))

        ax3.scatter(timeseries, gps[:, 4], c=c, edgecolor='none', s=3)
        ax3.set_xlim([timeseries.min(), timeseries.max()])
        ax3.xaxis.set_major_formatter(dates.DateFormatter('%H:%M:%S'))

        ax4.scatter(timeseries, gps[:, 6], c=c, edgecolor='none', s=3)
        ax4.set_xlim([timeseries.min(), timeseries.max()])
        ax4.xaxis.set_major_formatter(dates.DateFormatter('%H:%M:%S'))

        ax5.scatter(timeseries, gps[:, 5], c=c, edgecolor='none', s=3)
        ax5.set_xlim([timeseries.min(), timeseries.max()])
        ax5.xaxis.set_major_formatter(dates.DateFormatter('%H:%M:%S'))
        ax2.xaxis_date()
        ax3.xaxis_date()
        ax4.xaxis_date()
        ax5.xaxis_date()
        fig.autofmt_xdate()

        # add the legends
        ax1.legend(loc="best")

        ax1.set_ylabel('GPS northing [m]')
        ax1.set_xlabel('GPS easting [m]')
        ax2.set_ylabel('IMU heading over time [rad]')
        ax3.set_ylabel('GPS easting over time [m]')
        ax4.set_ylabel('GPS height over time [m]')
        ax5.set_ylabel('GPS northing over time [m]')

        fig.set_size_inches(16, 9)
        path = bb.make_job_file(gps_topic.replace("/", "_")+'.jpg')
        try:
            fig.savefig(path)
        except:
            logger.warn(gps[:, 4])
            logger.warn(gps[:, 5])
            logger.warn(gps[:, 6])
            raise
    return []
