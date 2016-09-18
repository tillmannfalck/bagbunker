# -*- coding: utf-8 -*-
#
# Copyright 2016 Robert Bosch GmbH, Renningen, Germany
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
from bagbunker import bb_bag

__version__ = '0.0.1'

TOPICS = [
    '/fredeluga/msf_core/odometry',
    '/matrice/dji_sdk/odometry',
    '/nibbio/msf_core/odometry',
    '/nibbio/vrpn_client/estimated_odometry',
    '/odom_corrected',
    '/robot/odom',
]


def detail_image_view(topic):
    @bb.detail()
    @bb.gallery_widget(title='Odometry ' + topic)
    def detail_images(fileset):
        jobrun = fileset.get_latest_jobrun('deepfield::odometry')
        if not jobrun:
            return None

        prefix = 'odometry_%s_' % topic.replace('/', '_')
        jobfiles = [x for x in jobrun.jobfiles
                    if x.name.startswith(prefix)]

        if not jobfiles:
            return None

        group, name = jobrun.name.split('::')
        return [{'alt': jobfile.name,
                 # XXX: this should be stored on jobfile or we could just
                 # return a jobfile instance
                 'src': '/'.join(['/marv/jobrun', group, name,
                                  str(jobrun.id), jobfile.name])
                 }
                for jobfile in jobfiles]


for topic in TOPICS:
    detail_image_view(topic)


@bb.job()
@bb_bag.messages(topics=TOPICS)
def job(fileset, messages):
    import numpy as np
    from collections import defaultdict

    class Info(object):
        def __init__(self):
            self.position = []
            self.lin_vel = []
            self.ang_vel = []
            self.time = []

    topics = defaultdict(Info)

    for topic, msg, timestamp in messages:
        pos = msg.pose.pose.position
        topics[topic].position.append([pos.x, pos.y, pos.z])

        twl = msg.twist.twist.linear
        twa = msg.twist.twist.angular

        topics[topic].lin_vel.append(np.linalg.norm([twl.x, twl.y, twl.z]))
        topics[topic].ang_vel.append(np.linalg.norm([twa.x, twa.y, twa.z]))

        topics[topic].time.append(msg.header.stamp.to_time())

    import matplotlib
    # don't attempt to use X11
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 2.5})

    for topic, info in topics.iteritems():
        position, lin_vel, ang_vel, time = map(
            np.array, (info.position, info.lin_vel, info.ang_vel, info.time))

        time -= time[0]
        position -= position[0, :]

        # plot velocities
        fig_vel, axs = plt.subplots(2, 1, sharex=True)
        ax_l, ax_a = axs

        ax_l.plot(time, lin_vel)
        ax_l.set_ylabel('linear velocity [m/s]')
        ax_l.locator_params(axis='y', nbins=5)

        ax_a.plot(time, ang_vel)
        ax_a.set_xlabel('time [s]')
        ax_a.set_ylabel('angular velocity [rad/s]')
        ax_a.locator_params(axis='y', nbins=5)

        fig_vel.tight_layout()

        axp = min([ax.yaxis.label.get_position()[0] for ax in axs])
        for ax in axs:
            ax.yaxis.set_label_coords(axp, .5, ax.yaxis.label.get_transform())

        # plot x-y position
        fig_pos, ax_pos = plt.subplots(1, 1)
        ax_pos.plot(position[:, 0], position[:, 1])
        ax_pos.set_xlabel('x position [m]')
        ax_pos.set_ylabel('y position [m]')

        # plot x,y,z over time
        fig_xyz, axs = plt.subplots(3, 1, sharex=True)
        ax_x, ax_y, ax_z = axs

        ax_x.plot(time, position[:, 0], label='x')
        ax_x.set_ylabel('x position [m]')
        ax_x.locator_params(axis='y', nbins=4)

        ax_y.plot(time, position[:, 1], label='y')
        ax_y.set_ylabel('y position [m]')
        ax_y.locator_params(axis='y', nbins=4)

        ax_z.plot(time, position[:, 2])
        ax_z.set_xlabel('time [s]')
        ax_z.set_ylabel('z position [m]')
        ax_z.locator_params(axis='y', nbins=4)

        fig_xyz.tight_layout()

        axp = min([ax.yaxis.label.get_position()[0] for ax in axs])
        for ax in axs:
            ax.yaxis.set_label_coords(axp, .5, ax.yaxis.label.get_transform())

        prefix = 'odometry_%s_' % topic.replace('/', '_')

        path_pos = bb.make_job_file(prefix + 'pos.png')
        path_xyz = bb.make_job_file(prefix + 'yz.png')
        path_vel = bb.make_job_file(prefix + 'vel.png')
        try:
            fig_pos.savefig(path_pos)
            fig_xyz.savefig(path_xyz)
            fig_vel.savefig(path_vel)
        except:
            logger.warn('could not create odometry plots for %s' % fileset)
            raise
        finally:
            plt.close(fig_pos)
            plt.close(fig_xyz)
            plt.close(fig_vel)

    return []
