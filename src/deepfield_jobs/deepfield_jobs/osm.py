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

from __future__ import absolute_import, division, print_function

import json
from marv import bb, db
from bagbunker import bb_bag

__version__ = '0.0.2'


@bb.job_model()
class Points(object):
    # json serialized [(quality, (lon, lat)), ...]
    data = db.Column(db.String, nullable=False)


@bb.job()
@bb_bag.messages(topics=('/zeno/gps/navsatfix',))
def job(fileset, messages):
    points = []
    for i, (topic, msg, timestamp) in enumerate(messages):
        # Whether to output an augmented fix is determined by both the fix
        # type and the last time differential corrections were received.  A
        # fix is valid when status >= STATUS_FIX.
        # STATUS_NO_FIX =  -1 -> unable to fix position       -> color id 0 = red
        # STATUS_FIX =      0 -> unaugmented fix              -> color id 1 = orange
        # STATUS_SBAS_FIX = 1 -> satellite-based augmentation -> color id 2 = blue
        # STATUS_GBAS_FIX = 2 -> ground-based augmentation    -> color id 3 = green
        #                     -> unknown status id            -> color id 4 = black
        if -1 <= msg.status.status <= 2:
            quality = msg.status.status + 1
        else:
            quality = 4
        point = (quality, (msg.longitude, msg.latitude))
        points.append(point)
    if points:
        yield Points(data=json.dumps(points))


@bb.detail()
@bb.osm_widget(title='OpenStreetMap Trajectory')
def osm_detail(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::osm')
    points = Points.query.filter(Points.jobrun == jobrun).first() \
        if jobrun is not None else None

    if not points:
        return

    # Build GeoJSON object
    features = []
    geo_json = {'type': 'FeatureCollection', 'features': features}
    prev_quality = None
    for quality, coord in json.loads(points.data):
        if quality != prev_quality:
            color = ('#f00', '#ffa500', '#00f', '#0f0', '#000')[quality]
            coordinates = []
            feat = {'type': 'Feature',
                    'properties': {'style': {'color': color}},
                    'geometry': {'type': 'LineString', 'coordinates': coordinates}}
            features.append(feat)
            prev_quality = quality
        coordinates.append(coord)

    return geo_json
