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

from deepfield_jobs.sanity_check import SanityCheck, Status
import json
import yaml


__version__ = '0.0.1'

# FIXME: sanity check config hardcoded for now
sanity_check_config = {'duration': {'min': 23},
                       'filesize': {'max': 3, 'min': 1},
                       'synced': {'jai': ['/camX/jai/nir/camera_info',
                                          '/camX/jai/nir/image_raw',
                                          '/camX/jai/rgb/camera_info',
                                          '/camX/jai/rgb/image_raw']},
                       'topics': {'/camX/jai/nir/camera_info': {'max': 21.5,
                                                                'min': 18.5},
                                  '/camX/jai/nir/image_raw': {'max': 21.5,
                                                              'min': 18.5},
                                  '/camX/jai/rgb/camera_info': {'max': 21.5,
                                                                'min': 18.5},
                                  '/camX/jai/rgb/image_raw': {'max': 21.5,
                                                              'min': 18.5},
                                  '/camX/siemens_logo/logo_light_state':
                                  {'min': 0.9},
                                  '/diagnostics_agg': {'min': 0},
                                  '/gps/fix': {'max': 21, 'min': 19},
                                  '/gps/heading': {'max': 21, 'min': 19},
                                  '/gps/info': {'max': 21, 'min': 19},
                                  '/gps/orientation': {'max': 21, 'min': 19},
                                  '/gps/time_reference': {'max': 21, 'min': 19},
                                  '/rosout_agg': {'min': 0},
                                  '/tf': {'min': 15}},
                       'tracklength': {'max': 7, 'min': 4.25}}

@bb.job_model()
class SanityCheckResult(object):
    results = db.Column(db.Text)
    success = db.Column(db.Boolean)


@bb.detail()
@bb.table_widget(title='Sanity Check')
@bb.column('name')
@bb.column('value')
@bb.column('status')
def sanity_check_detail(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::sanity_check_job')
    if jobrun is None:
        return None

    checks = SanityCheckResult.query.filter(SanityCheckResult.jobrun == jobrun)
    rows = []
    all_checks = checks.all()
    status_string_map = {
        Status.OK: 'OK',
        Status.TOHIGH: 'Too High',
        Status.TOLOW: 'Too low',
        Status.NONEXIST: 'Does not exist',
        Status.UNSYNCED: 'Unsynced',
        Status.ERROR: 'Error',
    }
    for c in all_checks:
        res_json = c.results
        res = json.loads(res_json)
        for entry in res:
            [name, value, status] = entry
            status_str = status_string_map[status]
            name_str = name
            if name.startswith('/'):
                # topic check
                name_str = 'Topic ' + name
                if name in sanity_check_config['topics']:
                    minmax = sanity_check_config['topics'][name]
                    if 'min' in minmax or 'max' in minmax:
                        interval = []
                        if 'min' in minmax:
                            interval.append('min: ' + str(minmax['min']))
                        if 'max' in minmax:
                            interval.append('max: ' + str(minmax['max']))
                        status_str = '%s [%s]' % (status_string_map[status], ', '.join(interval))
            rows.append({
                'name': name_str,
                'value': str(value),
                'status': status_str,
            })

        rows.append({'name': '<b>Summary</b>',
                     'value': '<b>-</b>',
                     'status': '<b>OK</b>' if c.success else '<b>Failed</b>',
                     })
    return rows


# FIXME: workaround until we have the module_name stored in the bag file as well
def extract_module_name(filename):
    basename = filename.split('/')[-1].split('.bag')[0]
    module = basename.split('__')[-1]
    if module in ['camA', 'camB', 'camC', 'main']:
        return module
    else:
        return ''

# FIXME: uses hardcoded config
def create_config(target_path):
    with open(target_path, 'w') as outfile:
        outfile.write(yaml.dump(sanity_check_config))


@bb.job()
@bb_bag.messages(topics=('/4dscan/scanrun',))
def job(fileset, messages):
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
            continue
        bagpath = fileset.dirpath + '/' + f.name
        logger.info('analysing bag file {0}, module name {1}'.format(bagpath,
                                                                     module_name))
        sc = SanityCheck()
        input_yaml = '/tmp/sanity_check.yaml'
        create_config(input_yaml)
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
