# -*- coding: utf-8 -*-
#
# Copyright 2015 Deepfield Robotics, Renningen, Germany
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
from bagbunker import bb_bag

__version__ = '0.0.1'

# FIXME: topics contain the sensor id as last element and thus can change;
#        we actually want all topics below /sensor/temperature/onewire
SENSOR_TOPICS = ('/sensor/temperature/onewire/28_4F7FCB060000',
                 '/sensor/temperature/onewire/28_7B36CB060000',
                 '/sensor/temperature/onewire/28_8B1BCB060000',
                 '/sensor/temperature/onewire/10_000802997784',
                 '/sensor/temperature/onewire/28_C279CC060000')


@bb.detail()
@bb.image_widget(title='Onewire Temperature')
def detail_image(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::onewire_temperature')
    if not jobrun:
        return None

    jobfiles = jobrun.jobfiles
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


@bb.job()
@bb_bag.messages(topics=SENSOR_TOPICS)
def job(fileset, messages):
    import datetime
    from collections import defaultdict
    tempmap = defaultdict(list)

    for topic, msg, timestamp in messages:
        now = datetime.datetime.fromtimestamp(msg.header.stamp.to_sec())
        sensorid = topic.split('/')[-1],
        tempmap[sensorid].append((now, msg.temperature))

    import matplotlib
    # don't attempt to use X11
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import dates

    fig = plt.figure()
    ax1 = fig.gca()
    ax1.xaxis.set_major_formatter(dates.DateFormatter('%H:%M:%S'))
    ax1.xaxis_date()
    fig.autofmt_xdate()

    for sensorid, templist in tempmap.iteritems():
        timestamps, temps = zip(*templist)
        ax1.plot(timestamps, temps, 'o-', label=sensorid[0])

    # add some margin
    xlim = ax1.get_xlim()
    ax1.set_xlim(dates.num2date(xlim[0])-datetime.timedelta(0, 2),
                 dates.num2date(xlim[1])+datetime.timedelta(0, 2))
    ylim = ax1.get_ylim()
    ax1.set_ylim(ylim[0]-2, ylim[1]+2)

    ax1.set_ylabel(u'Temperature [°C]')
    ax1.legend(bbox_to_anchor=(0.75, 1.13))
    path = bb.make_job_file('onewire_temperature.png')
    try:
        fig.savefig(path)
    except:
        logger.warn('could not create temperature plot for %s' % fileset)
        raise
    return []
