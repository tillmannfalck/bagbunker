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

import math
from marv import db, bb
from marv.bb import job_logger as logger
from marv.model import Jobrun
from bagbunker import bb_bag
import numpy as np

__version__ = '0.0.12'

# global list of topics
old_topics = ['/camera/image_raw_webcam',
              '/stereo_rgb/left/image_raw_sync',
              '/stereo_nir/left/image_raw_sync',
              '/stereo_rgb/right/image_raw_sync',
              '/stereo_nir/right/image_raw_sync',
              '/kinect2_center/ir/image_raw',
              '/kinect2_center/rgb/image_raw']
cams = ['camA', 'camB', 'camC']
new_topics = ['/%s/jai/rgb/image_raw' % cam for cam in cams] + \
             ['/%s/jai/nir/image_raw' % cam for cam in cams] + \
             ['/%s/kinect2/ir/image_raw' % cam for cam in cams] + \
             ['/%s/kinect2/rgb/image_raw' % cam for cam in cams]
flourish_topics = [
    '/fredeluga/cam0/image_raw',
    '/fredeluga/cam1/image_raw',
    '/guidance/left_image',
    '/guidance/right_image',
    'mono_rgb/image_raw',
    '/nibbio/camera/image_raw',
    '/nibbio/camera/image_raw_dropped',
    '/nibbio/camera/image_raw_sync',
    '/nibbio/tag_detections_image_dropped',
    '/sensor/jai/bayer/image_raw_sync',
    '/sensor/jai/nir/image_raw_sync',
    '/sensor/kinect2/sd/image_color_rect',
    '/sensor/kinect2/sd/image_depth',
    '/sensor/kinect2/sd/image_ir',
    '/sensor/laser/fx8/ir_image',
    '/sensor/laser/fx8/range_image',
    '/stereo_nir/left/image_raw_sync',
    '/stereo_rgb/left/image_raw_sync',
    '/thin_visensor_node/camera_left/image_raw',
    '/thin_visensor_node/camera_right/image_raw',
    '/ximea_asl/image_raw',
]
TOPICS = tuple(old_topics + new_topics + flourish_topics)

# @bb.job_model()
# class Video(object):
#     frame_count = db.Column(db.Integer)


# @bb.filter()
# @bb.filter_input('count', title='Number of frames', operators=comparisons,
#                  value_type='integer')
# def filter_count(query, count):
#     return query \
#         .join(Jobrun, aliased=True) \
#         .join(Video, aliased=True) \
#         .filter(compare(Video.frame_count, count.op, int(count.val)))


# @bb.summary()
# @bb.table_widget(title='Example camera summary')
# @bb.column('frame_count')
# @bb.column('image_count', title='Extracted images')
# def summary(filesets):
#     frame_count = db \
#         .session \
#         .query(db.func.sum(Video.frame_count)) \
#         .select_from(filesets.subquery()).first()[0]
#     image_count = filesets.join(Jobrun).join(Jobfile).count()
#     return [{
#         'frame_count': frame_count,
#         'image_count': image_count,
#     }]


def detail_image_view(topic):
    @bb.detail()
    @bb.gallery_widget(title='Images ' + topic)
    def detail_images(fileset):
        jobrun = fileset.get_latest_jobrun('deepfield::camera_frames')
        if not jobrun:
            return None

        jobfiles = [x for x in jobrun.jobfiles
                    if x.name.startswith('topic'+topic.replace("/", "_"))]

        if not jobfiles:
            return None

        group, name = jobrun.name.split('::')
        return [{'alt': jobfile.name,
                 # XXX: this should be stored on jobfile or we could just
                 # return a jobfile instance
                 'src': '/'.join(['/marv/jobrun', group, name,
                                  str(jobrun.id), jobfile.name]),
                 'width': 128}
                for jobfile in jobfiles]


for topic in TOPICS:
    detail_image_view(topic)


# @bb.listing()
# @bb.column('frame_count')
# def listing_video(fileset):
#     jobrun = fileset \
#         .jobruns \
#         .filter(Jobrun.name == 'deepfield::example_camera') \
#         .with_entities(Jobrun, db.func.max(Jobrun.id)).first()[0]
#     if jobrun is None or jobrun.deepfield__example_camera__video is None:
#         return {}
#     return {
#         'frame_count': jobrun.deepfield__example_camera__video.frame_count,
#     }


@bb.job()
@bb.config('max_frames', default=50, help="Maximum number of frames to extract")
@bb.config('image_width', default=320,
           help="Preview image width. Height is calculated via the aspect ratio.")
@bb_bag.messages(topics=TOPICS)
def job(fileset, messages, max_frames, image_width):
    import cv2
    import cv_bridge
    bridge = cv_bridge.CvBridge()

    topic_counts = dict((x.topic.name, x.msg_count) for x in fileset.bag.topics
                        if x.topic.name in TOPICS)
    intervals = dict((name, int(math.ceil(float(count) / max_frames)))
                     for name, count in topic_counts.items())
    msg_indexes = dict.fromkeys(topic_counts.keys(), 0)
    frame_indexes = dict.fromkeys(topic_counts.keys(), 0)
    logger.debug('Message counts %r', topic_counts)
    logger.debug('Intervals %r', intervals)
    for topic, msg, timestamp in messages:
        msg_idx = msg_indexes[topic]
        msg_indexes[topic] += 1
        if msg_idx % intervals[topic]:
            continue
        frame_idx = frame_indexes[topic]
        frame_indexes[topic] += 1
        image_name = bb.make_job_file(
            'topic{name}_{idx:03d}.jpg'.format(name=topic.replace('/', '_'),
                                               idx=frame_idx))

        if msg.encoding == '16UC1':
            cv_image = bridge.imgmsg_to_cv2(msg, "passthrough")
            cv_image = np.right_shift(cv_image, 8).astype(dtype=np.uint8)
        else:
            cv_image = bridge.imgmsg_to_cv2(msg, "rgb8")
        ratio = float(image_width) / float(cv_image.shape[1])
        scaled_img = cv2.resize(cv_image, (image_width, int(cv_image.shape[0]*ratio)),
                                interpolation=cv2.INTER_AREA)
        cv2.imwrite(image_name, scaled_img, (cv2.IMWRITE_JPEG_QUALITY, 60))
        logger.debug('saved %s', image_name)

    return []
