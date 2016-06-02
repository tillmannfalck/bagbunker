# -*- coding: utf-8 -*-
#
# Copyright 2016 Deepfield Robotics, Germany
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

from marv import db, bb
from marv import model
from marv.bb import job_logger as logger
from bagbunker import bb_bag

import os, sys
import json
import yaml

__version__ = '0.0.3'

HOME_PATH = os.path.expanduser("~")
# NOTE: this job requires a checkout of the full phenotyping repository in /home/bagbunker
SANITY_CHECK_PATH=HOME_PATH + '/phenotyping/phenotyping_diagnostics/scripts/'
sys.path.append(SANITY_CHECK_PATH)

def get_config_filename(mode):
    return SANITY_CHECK_PATH + 'sanity_check_%s.yaml' % mode

@bb.job_model()
class SanityCheckResult(object):
    results = db.Column(db.Text)
    success = db.Column(db.Boolean)


# FIXME: workaround until we have the module_name and mode stored in the bag file
def extract_mode(filename):
    segments = filename.split('.')[0].split('__')
    if filename.endswith('__main.bag'):
        if len(segments) < 5:
            return ''
        return segments[-1]
    else:
        if len(segments) < 7:
            return ''
        return segments[-4]


def extract_module_name(filename):
    if not filename.endswith('.bag'):
        return ''
    basename = filename.split('/')[-1].split('.bag')[0]
    module = basename.split('__')[-1]
    if module in ['camA', 'camB', 'camC', 'main']:
        return module
    else:
        return ''


@bb.detail()
@bb.table_widget(title='Sanity Check')
@bb.column('name')
@bb.column('value')
@bb.column('status')
@bb.column('expected')
def sanity_check_detail(fileset):
    from sanity_check import Status

    jobrun = fileset.get_latest_jobrun('deepfield::sanity_check_job')
    if jobrun is None:
        return None

    checks = SanityCheckResult.query.filter(SanityCheckResult.jobrun == jobrun)
    rows = []
    all_checks = checks.all()
    status_string_map = {
        Status.OK: 'OK',
        Status.TOOHIGH: 'Too High',
        Status.TOOLOW: 'Too low',
        Status.NONEXIST: 'Does not exist',
        Status.UNSYNCED: 'Unsynced',
        Status.ERROR: 'Error',
        Status.SPEEDTOOLOW: 'Speed too low',
        Status.SPEEDTOOHIGH: 'Speed too high',
    }
    # XXX: we only consider 'single bag' filesets
    bagfilename = fileset.files[0].name
    mode = extract_mode(bagfilename)
    module_name = extract_module_name(bagfilename)
    with open(get_config_filename(mode), 'r') as config_file:
        check_config = yaml.load(config_file)

    def get_cfg_interval(minmax):
        interval = []
        if 'min' in minmax or 'max' in minmax:
            if 'min' in minmax:
                interval.append('min: ' + str(minmax['min']))
            if 'max' in minmax:
                interval.append('max: ' + str(minmax['max']))
        return interval

    for c in all_checks:
        res_json = c.results
        res = json.loads(res_json)
        for entry in res:
            [name, value, status] = entry
            status_str = status_string_map[status]
            name_str = name
            interval = []
            if name.startswith('/'):
                name_str = 'Topic ' + name
                cfg_key = name
                # in sanity check config, camX stands for camA,B,C topics
                if name.startswith('/cam'):
                    cfg_key = name.replace(module_name, 'camX')
                if cfg_key in check_config['topics']:
                    minmax = check_config['topics'][cfg_key]
                    interval = get_cfg_interval(minmax)
            else:
                possible_cfg_key = name.lower()
                if possible_cfg_key in check_config:
                    minmax = check_config[possible_cfg_key]
                    interval = get_cfg_interval(minmax)
            rows.append({
                'name': name_str,
                'value': str(value),
                'status': status_str,
                'expected': ', '.join(interval) if interval else '-',
            })

        rows.append({'name': '<b>Summary</b>',
                     'value': '<b>-</b>',
                     'status': '<b>OK</b>' if c.success else '<b>Failed</b>',
                    })
    return rows


@bb.job()
@bb_bag.messages(topics=('/4dscan/scanrun',))
def job(fileset, messages):
    try:
        from sanity_check import SanityCheck, Status
    except ImportError:
        logger.info('Sanity check module not found. Is there a phenotyping checkout in %s?' %
                    HOME_PATH)
        raise

    # first, make sure that the 'invalid' tag exists
    tg_qry = model.Tag.query.filter(model.Tag.label == 'invalid').first()
    tg = None
    if tg_qry:
        tg = tg_qry
    else:
        tg = model.Tag(label='invalid')
        db.session.commit()

    for f in fileset.files:
        module_name = extract_module_name(f.name)
        if not module_name:
            logger.info('could not extract module name from %s, skipping' % f.name)
            continue
        mode = extract_mode(f.name)
        if not mode:
            logger.info('could not extract measurement mode from %s, skipping' % f.name)
            continue
        bagpath = fileset.dirpath + '/' + f.name
        logger.info('analysing bag file {0}, module name {1}'.format(bagpath,
                                                                     module_name))
        sc = SanityCheck()
        # expects configurations to be in the same path
        input_yaml = get_config_filename(mode)
        result = sc.analyse_bag_file(bagpath, input_yaml, module_name)
        success = True
        for check in result:
            if check[2] != Status.OK and check[2] != Status.TOHIGH:
                success = False
                break
        logger.info('result: %s' % json.dumps(result))
        contains_qry = model.Tag.query.filter(model.Tag.filesets.contains(fileset)).first()
        if contains_qry and success:
            # remove tag
            tg.filesets.remove(fileset)
        elif not contains_qry and not success:
            # add tag
            tg.filesets.append(fileset)
        db.session.commit()

        yield SanityCheckResult(results=json.dumps(result),
                                success=success)
