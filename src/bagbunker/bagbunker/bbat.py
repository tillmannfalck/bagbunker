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

import click
import logging
import requests
import rosbag
import rospy
import socket
from roslib.message import get_message_class
from rosgraph_msgs.msg import Clock
from marv.log import loglevel_option
from .reader import MessageStreamClient


@click.group()
@loglevel_option(default='info')
@click.pass_context
def bbmsg(ctx, loglevel):
    try:
        rospy.set_param('use_sim_time', True)
    except socket.error, e:
        if e.errno == 111:
            click.echo('Error connecting to roscore, has it been started?')
        else:
            import traceback
            click.echo(traceback.format_exc(e))
        ctx.exit(e.errno)
    rospy.init_node('bbmsg')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(loglevel)


@bbmsg.command()
@click.argument('url', required=True)
@click.pass_context
def play(ctx, url):
    """Like rosbag play, streaming from bagbunker.

    example URLs:

    http://bagbunker.int.bosppaa.com/api/messages/<md5>
    http://bagbunker.int.bosppaa.com/api/messages/<md5>?topic=/foo
    http://bagbunker.int.bosppaa.com/api/messages/<md5>?topic=/foo&topic=/bar
    """
    logger = logging.getLogger('bbmsg.play')

    resp = requests.get(url, stream=True,
                        headers={'Accept': 'application/x-ros-bag-msgs'})
    if resp.status_code != 200:
        raise Exception(resp)

    msc = MessageStreamClient(resp.iter_content(chunk_size=512))
    topics = msc.topics
    if '/clock' in topics:
        raise ValueError('/clock may not be streamed from server')

    # XXX: verify md5 sum
    pubs = {topic_id: rospy.Publisher(topic, get_message_class(msg_type), queue_size=1)
            for topic, (topic_id, msg_type, mt_md5sum) in topics.items()}
    clock_pub = rospy.Publisher('/clock', Clock, queue_size=1)

    clock_msg = Clock()
    for topic_id, nsec, data in msc.messages:
        time = rospy.rostime.Time.from_sec(nsec * 1e-9)
        clock_msg.clock = time
        clock_pub.publish(clock_msg)

        pub = pubs[topic_id]
        msg = pub.data_class()
        msg.deserialize(data)
        logger.debug('Publishing: %r', msg)
        pub.publish(msg)

        if rospy.is_shutdown():
            logger.warn('Aborting due to rospy shutdown.')
            ctx.exit(108)

    logger.info('Finished publishing')
    rospy.signal_shutdown('Finished publishing')
    rospy.spin()


@bbmsg.command('fetch-bag')
@click.option('--lz4/--no-lz4', help='Use lz4 compression in saved bag')
@click.argument('url', required=True)
@click.pass_context
def fetch_bag(ctx, lz4, url):
    """fetch custom filtered bag from bagbunker

    example URLS:

    http://bagbunker.int.bosppaa.com/api/messages/<md5>
    http://bagbunker.int.bosppaa.com/api/messages/<md5>?topic=/foo
    http://bagbunker.int.bosppaa.com/api/messages/<md5>?topic=/foo&topic=/bar
    """
    logger = logging.getLogger('bbmsg.fetch-bag')

    resp = requests.get(url, stream=True,
                        headers={'Accept': 'application/x-ros-bag-msgs'})
    if resp.status_code != 200:
        raise Exception(resp)

    msc = MessageStreamClient(resp.iter_content(chunk_size=512))
    path = '{}.bag'.format(msc.name)
    bag = rosbag.Bag(path, 'w', compression='lz4' if lz4 else 'none')

    topics = {topic_id: (topic, msg_type, mt_md5sum)
              for topic, (topic_id, msg_type, mt_md5sum) in msc.topics.items()}

    for topic_id, nsec, data in msc.messages:
        logger.debug('Message size: %s', len(data))
        time = rospy.rostime.Time.from_sec(nsec * 1e-9)
        topic, msg_type, mt_md5sum = topics[topic_id]
        msg = (msg_type, data, mt_md5sum, None)
        bag.write(topic, msg, time, raw=True)

    logger.info('Finished writing bag %s', path)
    bag.close()
    rospy.signal_shutdown('Finished publishing')
    rospy.spin()


def cli():
    bbmsg(auto_envvar_prefix='BBMSG')


if __name__ == '__main__':
    cli()
