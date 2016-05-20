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
from bagbunker import bb_bag
import json

__version__ = '0.0.1'

@bb.job_model()
class CPU_Diagnostics(object):
    data = db.Column(db.Text)

@bb.detail()
@bb.table_widget(title='CPU Diagnostics', sort='name')
@bb.column('name')
@bb.column('average load')
@bb.column('maximum load')
@bb.column('average temperature')
@bb.column('maximum temperature')
def diagnostics_detail(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::cpu_diagnostics')
    if jobrun is None:
        return None

    diags = CPU_Diagnostics.query.filter(CPU_Diagnostics.jobrun == jobrun)
    rows = []
    for diag in diags:
        statistics = json.loads(diag.data)

        for key, values in statistics.items():
            rows.append({
                'name': key,
                'average load': values[0][0],
                'maximum load': values[0][1],
                'average temperature': values[1][0],
                'maximum temperature': values[1][1],
            })
    return rows

def cpu_load_statistics(diagnostics_array):
    import numpy as np
    cpu_load_history = list()

    for entry in diagnostics_array:
        cpu_load_set = list()

        core_id = 0
        valid_core = True

        while valid_core:
            try:
                cpu_idle_str = "CPU " + str(core_id) + " Idle"
                cpu_load = 100 - float(entry[cpu_idle_str])
                cpu_load_set.append(cpu_load)
                core_id += 1
            except KeyError:
                valid_core = False

        cpu_load_history.append(cpu_load_set)

    cpu_load_max = np.max([np.average(i) for i in cpu_load_history])
    cpu_load_avg = np.average([np.average(i) for i in cpu_load_history])

    return int(cpu_load_avg), int(cpu_load_max)

def cpu_temp_statistics(diagnostics_array):
    import numpy as np
    cpu_temp_history = list()

    for entry in diagnostics_array:
        cpu_temp_set = list()

        sensor_id = 0
        valid_sensor = True

        while valid_sensor:
            try:
                cpu_temp_str = "Core " + str(sensor_id) + " Temp"
                cpu_temp = float(entry[cpu_temp_str])
                cpu_temp_set.append(cpu_temp)
                sensor_id += 1
            except KeyError:
                valid_sensor = False

        cpu_temp_history.append(cpu_temp_set)

    cpu_temp_max = np.max([np.max(i) for i in cpu_temp_history])
    cpu_temp_avg = np.average([np.average(i) for i in cpu_temp_history])

    return int(cpu_temp_avg), int(cpu_temp_max)

@bb.job()
@bb_bag.messages(topics=('/diagnostics_agg',))
def job(_, messages):
    load_statistics = dict()
    temp_statistics = dict()
    statistics = dict()

    for _, msg, _ in messages:
        for stat in msg.status:
            if "CPU Usage" in stat.name:
                status_info = dict()
                for key_value_pair in stat.values:
                    status_info[key_value_pair.key] = key_value_pair.value
                if not stat.name[1:5] in load_statistics:
                    load_statistics[stat.name[1:5]] = list()
                load_statistics[stat.name[1:5]].append(status_info)
            if "CPU Temperature" in stat.name:
                # exclude odroid
                if not "odroid" in stat.hardware_id:
                    status_info = dict()
                    for key_value_pair in stat.values:
                        status_info[key_value_pair.key] = key_value_pair.value
                    if not stat.name[1:5] in temp_statistics:
                        temp_statistics[stat.name[1:5]] = list()
                    temp_statistics[stat.name[1:5]].append(status_info)

    for key in temp_statistics:
        statistics[key] = [cpu_load_statistics(load_statistics[key]), cpu_temp_statistics(temp_statistics[key])]

    yield CPU_Diagnostics(data=json.dumps(statistics))
