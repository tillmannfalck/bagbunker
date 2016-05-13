from __future__ import absolute_import, division

from collections import defaultdict
from marv import db, bb
from bagbunker import bb_bag
# import json
import numpy as np

__version__ = '0.0.10'

@bb.job_model()
class CPU_Diagnostics(object):
    name = db.Column(db.Text)
    average = db.Column(db.Integer)
    maximum = db.Column(db.Integer)

@bb.detail()
@bb.table_widget(title='CPU Diagnostics', sort='name')
@bb.column('name')
@bb.column('average')
@bb.column('maximum')
def diagnostics_detail(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::cpu_diagnostics')
    if jobrun is None:
        return None

    diags = CPU_Diagnostics.query.filter(CPU_Diagnostics.jobrun == jobrun)
    rows = []
    for diag in diags:
        if diag.average:
            rows.append({
                'name': diag.name,
                'average': diag.average,
                'maximum': diag.maximum,
            })
    return rows

def cpu_load_statistics(diagnostics_array):
    cpu_load_history = list()
    cpu_load_max = list()
    cpu_load_avg = list()

    for entry in diagnostics_array:
        cpu_load_set = list()

        for cpu_core in range(0, CORES):
            cpu_idle_str = "CPU " + str(cpu_core) + " Idle"
            cpu_load = 100 - float(entry[cpu_idle_str])
            cpu_load_set.append(cpu_load)
        cpu_load_history.append(cpu_load_set)

    for cpu_core in range(0, CORES):
        cpu_load_max.append(np.max([i[cpu_core] for i in cpu_load_history]))
        cpu_load_avg.append(np.average([i[cpu_core] for i in cpu_load_history]))

    return np.max(cpu_load_avg), np.average(cpu_load_max)

def cpu_temp_statistics(diagnostics_array):
    cpu_temp_history = list()
    cpu_temp_max = list()
    cpu_temp_avg = list()

    for entry in diagnostics_array:
        cpu_temp_set = list()

        for sensor in range(0, TEMP_SENSORS):
            cpu_temp_str = "Core " + str(sensor) + " Temp"
            cpu_temp = float(entry[cpu_temp_str])
            cpu_temp_set.append(cpu_temp)
        cpu_temp_history.append(cpu_temp_set)

    for cpu_core in range(0, TEMP_SENSORS):
        cpu_temp_max.append(np.max([i[cpu_core] for i in cpu_temp_history]))
        cpu_temp_avg.append(np.average([i[cpu_core] for i in cpu_temp_history]))

    return np.max(cpu_temp_avg), np.average(cpu_temp_max)

CORES = 4
TEMP_SENSORS = 2

@bb.job()
@bb_bag.messages(topics=('/diagnostics',))
def job(fileset, messages):
    load_statistics = defaultdict()
    temp_statistics = defaultdict()
    statistics = defaultdict()
    statistics_list = list()

    for _, msg, _ in messages:
        for stat in msg.status:
            if "cpu_monitor CPU Usage" in stat.name:
                status_info = dict()
                for key_value_pair in stat.values:
                    status_info[key_value_pair.key] = key_value_pair.value
                if not stat.name in load_statistics:
                    load_statistics[stat.name] = list()
                load_statistics[stat.name].append(status_info)
            if "cpu_monitor CPU Temperature" in stat.name:
                status_info = dict()
                for key_value_pair in stat.values:
                    status_info[key_value_pair.key] = key_value_pair.value
                if not stat.name in temp_statistics:
                    temp_statistics[stat.name] = list()
                temp_statistics[stat.name].append(status_info)

    for name, load_history in load_statistics.items():
        statistics[name] = cpu_load_statistics(load_history)
        statistics_list.append([name, load_history[0], load_history[1]])

    for name, temp_history in temp_statistics.items():
        statistics[name] = cpu_temp_statistics(temp_history)
        statistics_list.append([name, temp_history[0], temp_history[1]])

    for name, cpu_values in statistics.items():
        yield CPU_Diagnostics(name=name,
                              average=cpu_values[0],
                              maximum=cpu_values[1])
