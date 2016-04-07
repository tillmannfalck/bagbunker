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

import os
from marv import bb, db
from marv.bb import job_logger as logger
from marv.model import Fileset, Jobrun
from bagbunker import bb_bag

__version__ = '0.0.2'

# open issues:
# - for additional files & label file:
#   - relative path or absolute path
#   - allow downloading
# - nicer display (esp. of weeds list)

metadata_weeds = db.Table(
    'metadata_weeds',
     db.Column('metadata_id', db.Integer, db.ForeignKey('deepfield__metadata__metadata.id'), nullable=False),
     db.Column('weed_id', db.Integer, db.ForeignKey('weed.id'), nullable=False))

metadata_additionalfiles = db.Table(
    'metadata_additionalfiles',
    db.Column('metadata_id', db.Integer, db.ForeignKey('deepfield__metadata__metadata.id'), nullable=False),
    db.Column('additionalfile_id', db.Integer, db.ForeignKey('additionalfile.id'), nullable=False)
)

@bb.job_model()
class Metadata(object):
    # the id column is created automatically by the decorator
    robot_name = db.Column(db.String(42), nullable=False)
    plot = db.Column(db.String(126), nullable=False)
    crop = db.Column(db.String(100), nullable=False)
    bbch_growth = db.Column(db.Integer)
    row_spacing_inter = db.Column(db.Integer)
    row_spacing_intra = db.Column(db.Integer)
    label_file = db.Column(db.String(100), nullable=True)
    weeds = db.relationship('Weed', secondary=metadata_weeds)
    additional_files = db.relationship('AdditionalFile', secondary=metadata_additionalfiles)

class Weed(db.Model):
    __tablename__ = 'weed'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(126), nullable=False, unique=True)

class AdditionalFile(db.Model):
    __tablename__ = 'additionalfile'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(126), nullable=False, unique=True)

@bb.job()
@bb_bag.messages(topics=())
def job(fileset, messages):
    if not fileset.bag:
        return
    import yaml

    logger.info('job version: %s' % __version__)

    metadata_filename = '%s/%s.yml' % (fileset.dirpath, fileset.name)
    logger.info('looking for %s' % metadata_filename)
    # default values
    robot_name = '(unknown)'
    plot= '(unknown)'
    crop = '(unknown)'
    bbch_growth = None
    row_spacing_inter = None
    row_spacing_intra = None
    label_file = None
    weeds = []
    additional_files = []

    if os.path.isfile(metadata_filename):
        with open(metadata_filename) as infile:
            metadata = yaml.load(infile)
        logger.info('metadata: %s' % metadata)
        robot_name = metadata.get('robot', '(unknown)')
        plot = metadata.get('plot_name', '(unknown)')
        crop = metadata.get('crop', '(unknown)')
        bbch_growth = int(metadata.get('bbch_growth', 0))
        if 'row_spacing' in metadata:
            rs = metadata['row_spacing']
            row_spacing_inter = int(rs.get('inter', None))
            row_spacing_intra = int(rs.get('intra', None))
        label_file = metadata.get('label_file', None)
        # make sure that we don't add duplicate entries
        for weedname in metadata.get('weed_species', []):
            weed_qry = Weed.query.filter(Weed.name == weedname).first()
            weeds.append(weed_qry if weed_qry else Weed(name=weedname))
        for additional_file in metadata.get('additional_files', []):
            afile_qry = AdditionalFile.query.filter(AdditionalFile.name == additional_file).first()
            additional_files.append(afile_qry if afile_qry else AdditionalFile(name=additional_file))

    yield Metadata(robot_name=robot_name, plot=plot, crop=crop, bbch_growth=bbch_growth,
                   row_spacing_inter=row_spacing_inter, row_spacing_intra=row_spacing_intra,
                   label_file=label_file, weeds=weeds, additional_files=additional_files)

@bb.filter()
@bb.filter_input('robot', operators=['substring'])
def filter_robot(query, ListingEntry, robot):
    return query.filter(ListingEntry.robot.contains(robot.val))


@bb.filter()
@bb.filter_input('plot', operators=['substring'])
def filter_plot(query, ListingEntry, plot):
    return query.filter(ListingEntry.plot.contains(plot.val))

@bb.listing()
@bb.listing_column('robot')
@bb.listing_column('plot')
def listing(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::metadata')
    if jobrun is None:
        return {}

    meta = Metadata.query.filter(Metadata.jobrun == jobrun).first()
    if meta is None:
        return {}
    return {
        'robot': meta.robot_name,
        'plot': meta.plot,
    }
