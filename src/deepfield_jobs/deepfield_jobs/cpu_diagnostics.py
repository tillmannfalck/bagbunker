from __future__ import absolute_import, division

from collections import defaultdict
from marv import db, bb
from bagbunker import bb_bag
import json
import numpy as np

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
    cpu_load_history = list()

    for entry in diagnostics_array:
        cpu_load_set = list()

        for cpu_core in range(0, CORES):
            cpu_idle_str = "CPU " + str(cpu_core) + " Idle"
            cpu_load = 100 - float(entry[cpu_idle_str])
            cpu_load_set.append(cpu_load)
        cpu_load_history.append(cpu_load_set)

    cpu_load_max = np.max([np.average(i) for i in cpu_load_history])
    cpu_load_avg = np.average([np.average(i) for i in cpu_load_history])

    return int(cpu_load_avg), int(cpu_load_max)

def cpu_temp_statistics(diagnostics_array):
    cpu_temp_history = list()

    for entry in diagnostics_array:
        cpu_temp_set = list()

        for sensor in range(0, TEMP_SENSORS):
            cpu_temp_str = "Core " + str(sensor) + " Temp"
            cpu_temp = float(entry[cpu_temp_str])
            cpu_temp_set.append(cpu_temp)
        cpu_temp_history.append(cpu_temp_set)

    cpu_temp_max = np.max([np.max(i) for i in cpu_temp_history])
    cpu_temp_avg = np.average([np.average(i) for i in cpu_temp_history])

    return int(cpu_temp_avg), int(cpu_temp_max)

CORES = 4
TEMP_SENSORS = 2

@bb.job()
@bb_bag.messages(topics=('/diagnostics_agg',))
def job(_, messages):
    load_statistics = defaultdict()
    temp_statistics = defaultdict()
    statistics = defaultdict()

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
