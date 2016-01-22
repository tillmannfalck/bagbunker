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
import os
import requests
import rosbag
import rospy
import socket
import genpy
from roslib.message import get_message_class
from rosgraph_msgs.msg import Clock
from .reader import MessageStreamClient


@click.group()
def bbmsg():
    pass


@bbmsg.command()
@click.argument('url', required=True)
@click.pass_context
def play(ctx, url):
    """Like rosbag play, streaming from bagbunker.

    example URLs:

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>?topic=/foo

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>?topic=/foo&topic=/bar

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>?topic=/foo&msg_type=std_msgs/String

    (topic1 OR topic2) AND (msg_type1 OR msg_type2)
    """
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

    resp = requests.get(url, stream=True,
                        headers={'Accept': 'application/x-ros-bag-msgs'})
    if resp.status_code != 200:
        raise Exception(resp)

    msc = MessageStreamClient(resp.iter_content(chunk_size=512))
    topics = msc.topics
    if '/clock' in topics:
        raise ValueError('/clock must not be streamed from server')

    pubs = {}
    missing = []
    for topic, msg_type in topics.items():
        pytype = get_message_class(msg_type)
        if pytype is None:
            missing.append(msg_type)
            continue
        pubs[topic] = rospy.Publisher(topic, pytype, queue_size=1)
    if missing:
        missing.sort()
        click.echo("Missing message types:\n" + '\n   '.join(missing))
        ctx.exit(2)

    clock_pub = rospy.Publisher('/clock', Clock, queue_size=1)

    clock_msg = Clock()
    for topic, secs, nsecs, raw_msg in msc.messages:
        time = genpy.Time(secs, nsecs)
        clock_msg.clock = time
        clock_pub.publish(clock_msg)

        pub = pubs[topic]
        assert pub.md5sum == raw_msg[2]
        msg = pub.data_class()
        msg.deserialize(raw_msg[1])
        pub.publish(msg)

        if rospy.is_shutdown():
            click.echo('Aborting due to rospy shutdown.')
            ctx.exit(108)

    click.echo('Finished publishing')
    rospy.signal_shutdown('Finished publishing')
    rospy.spin()


@bbmsg.command('fetch-bag')
@click.option('--lz4/--no-lz4', help='Use lz4 compression in saved bag')
@click.argument('url', required=True)
@click.pass_context
def fetch_bag(ctx, lz4, url):
    """fetch custom filtered bag from bagbunker

    example URLS:

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>?topic=/foo

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>?topic=/foo&topic=/bar

    http://bagbunker.int.bosppaa.com/marv/api/messages/<md5>?topic=/foo&msg_type=std_msgs/String

    (topic1 OR topic2) AND (msg_type1 OR msg_type2)
    """
    resp = requests.get(url, stream=True,
                        headers={'Accept': 'application/x-ros-bag-msgs'})
    if resp.status_code != 200:
        raise Exception(resp)

    msc = MessageStreamClient(resp.iter_content(chunk_size=512))
    missing = []
    for topic, msg_type in msc.topics.items():
        if get_message_class(msg_type) is None:
            missing.append(msg_type)
            continue
    if missing:
        missing.sort()
        click.echo("Missing message types:\n" + '\n   '.join(missing))
        ctx.exit(2)

    path = '{}.bag'.format(msc.name)
    if os.path.exists(path):
        click.echo('Will not overwrite existing bag: ' + path)
        ctx.exit(-1)
    bag = rosbag.Bag(path, 'w', compression='lz4' if lz4 else 'none')

    for topic, secs, nsecs, raw_msg in msc.messages:
        time = genpy.Time(secs, nsecs)
        # This will need the correct message classes available
        bag.write(topic, raw_msg, time, raw=True)

    click.echo('Finished writing bag %s' % path)


def cli():
    bbmsg(auto_envvar_prefix='BBMSG')


if __name__ == '__main__':
    cli()
