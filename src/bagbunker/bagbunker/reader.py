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

import cPickle as pickle
from marv import bb, db
from collections import OrderedDict, defaultdict
from datetime import datetime
from functools import partial
from logging import getLogger
from .model import Bag, BagMsgType, BagTopic, BagTopics


@bb.reader(Bag)
def reader(fileset):
    logger = getLogger('{}.{}'.format(__name__, fileset.name))
    logger.debug('start')
    import rosbag
    starttime = None
    endtime = None
    topics = defaultdict(int)
    for file in fileset.files:
        logger.debug('opening %s', file.path)
        rbag = rosbag.Bag(file.path)

        # We are assuming the timestamps are in local time
        if not starttime:
            starttime = datetime.fromtimestamp(rbag.get_start_time())
        endtime = datetime.fromtimestamp(rbag.get_end_time())

        logger.debug('reading topic info %s', file.path)
        info = rbag.get_type_and_topic_info()
        for tname, topic in info.topics.items():
            topics[tname, topic.msg_type] += topic.message_count

        rbag.close()

    logger.debug('topic info %r', topics)
    # We assume that files of a set are meant to be consecutive
    duration = endtime - starttime

    # Create missing msg_types/topics and assemble lists
    bag_topics = []
    for (name, msg_type_name), count in topics.items():
        topic = db.session.query(BagTopic).filter(BagTopic.name == name).first()
        if topic is None:
            topic = BagTopic(name=name)
            db.session.add(topic)

        msg_type = db.session.query(BagMsgType) \
                             .filter(BagMsgType.name == msg_type_name).first()
        if msg_type is None:
            msg_type = BagMsgType(name=msg_type_name)
            db.session.add(msg_type)

        bag_topics.append(BagTopics(msg_count=count, msg_type=msg_type, topic=topic))

    logger.debug('done')
    # msecs = ((duration.days * 24 * 3600 + duration.seconds) * 10**6 +
    #          duration.microseconds) / 10**3
    return Bag(starttime=starttime, endtime=endtime,
               duration=duration, topics=bag_topics)


@reader.http_messages_generator
def http_messages(fileset, topic=(), msg_type=(), start_time=None,
                  end_time=None, logger=None, accept_mimetypes=None):
    """Iterate over fileset's messages, optionally filtered by topic
    and/or message type.
    """
    import flask
    import rosbag
    from roslib.message import get_message_class

    topics = {name: (topic_id, msg_type, get_message_class(msg_type)._md5sum)
              for topic_id, (name, msg_type)
              in enumerate((x.topic.name, x.msg_type.name) for x in fileset.bag.topics)
              if name in topic or not topic}
    meta = {'topics': topics,
            'name': fileset.name}

    def read_messages(**kw):
        logger.debug('start reading messages %s', kw)
        for file in fileset.files:
            logger.debug('opening %s', file.path)
            rbag = rosbag.Bag(file.path)
            for x in rbag.read_messages(**kw):
                yield x
            rbag.close()
            logger.debug('closed %s', file.path)
        logger.debug('done reading messages %s', kw)

    def x_ros_bag_msgs(raw_messages):
        logger.debug('start streaming')

        yield pickle.dumps(meta, protocol=2)

        for topic, raw_msg, timestamp in raw_messages:
            topic_id = topics[topic][0]
            data = raw_msg[1]
            yield pickle.dumps((topic_id, timestamp.to_nsec(), data), protocol=2)
        logger.debug('done streaming')

    # in a previous implementation there were two mimetypes. Keeping
    # the code with bad/request dummy in case we need more mimetypes
    handler = OrderedDict((
        ('*/*', x_ros_bag_msgs),
        ('foo/bar', lambda x: 'foobar'),
        ('application/x-ros-bag-msgs', x_ros_bag_msgs),
    ))

    # accept_mimetypes are in order of quality. If not specified use
    # our first, otherwise first matching. Raise exception if no
    # matching mimetype
    accept_mimetypes = accept_mimetypes or (handler.iteritems().next(),)
    try:
        mimetype = (mimetype for mimetype, quality in accept_mimetypes
                    if mimetype in handler).next()
    except StopIteration:
        logger.error('No matching mimetype: %r', accept_mimetypes)
        flask.abort(400)

    # start streaming
    messages = handler[mimetype](read_messages(topics=topic or None,
                                               start_time=start_time,
                                               end_time=end_time,
                                               raw=True))
    mimetype = 'application/x-ros-bag-msgs' if mimetype == '*/*' else mimetype
    return messages, mimetype


class MessageStreamClient(object):
    def __init__(self, chunks):
        self.chunks = chunks
        self.current = chunks.next()
        self.messages = self._gen()
        self.meta = self.messages.next()
        self.name = self.meta['name']
        self.topics = self.meta['topics']

    def _gen(self):
        while True:
            try:
                yield pickle.load(self)
            except EOFError:
                break

    def read(self, n):
        current = self.current
        while n > len(current):
            try:
                current += self.chunks.next()
            except StopIteration:
                break
        rv = current[:n]
        self.current = current[n:]
        return rv

    def readline(self):
        # Effectively blocking load_global(), i.e. arbitrary types
        raise NotImplementedError
