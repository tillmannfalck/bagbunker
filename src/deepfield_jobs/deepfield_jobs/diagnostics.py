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

from collections import defaultdict
from marv import db, bb
from bagbunker import bb_bag


__version__ = '0.0.1'


@bb.job_model()
class Diagnostics(object):
    name = db.Column(db.Text)
    ok_count = db.Column(db.Integer)
    warn_count = db.Column(db.Integer)
    error_count = db.Column(db.Integer)


@bb.detail()
@bb.table_widget(title='Diagnostics', sort='name')
@bb.column('name')
@bb.column('count')
@bb.column('status')
def diagnostics_detail(fileset):
    jobrun = fileset.get_latest_jobrun('deepfield::diagnostics')
    if jobrun is None:
        return None

    diags = Diagnostics.query.filter(Diagnostics.jobrun == jobrun)
    rows = []
    for diag in diags:
        if diag.ok_count:
            rows.append({
                'name': diag.name,
                'count': diag.ok_count,
                'status': 'OK',
            })
        if diag.warn_count:
            rows.append({
                'name': diag.name,
                'count': diag.warn_count,
                'status': 'WARN',
            })
        if diag.error_count:
            rows.append({
                'name': diag.name,
                'count': diag.error_count,
                'status': 'ERROR',
            })
    return rows


@bb.job()
@bb_bag.messages(topics=('/diagnostics',))
def job(fileset, messages):
    from diagnostic_msgs.msg import DiagnosticStatus

    class DiagCounter(object):
        def __init__(self):
            self.oks = 0
            self.errors = 0
            self.warnings = 0
    diagcounters = defaultdict(DiagCounter)

    for topic, msg, timestamp in messages:
        for stat in msg.status:
            if stat.level == DiagnosticStatus.OK:
                diagcounters[stat.name].oks += 1
            elif stat.level == DiagnosticStatus.WARN:
                diagcounters[stat.name].warnings += 1
            else:
                diagcounters[stat.name].errors += 1

    for name, diagcounter in diagcounters.items():
        yield Diagnostics(name=name,
                          ok_count=diagcounter.oks,
                          warn_count=diagcounter.warnings,
                          error_count=diagcounter.errors)
