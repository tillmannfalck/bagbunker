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

import inspect
import logging
import os
from flask import current_app
from .globals import _job_ctx_stack
from .model import db, Jobfile, Jobrun
from .parameters import Config
from .widgeting import ParameterBase, WidgetBase


MODELS = []


class JobContext(object):
    def __init__(self, jobrun_id, group, name):
        logger_name = '{}.{}.{}'.format(__name__, group, name)
        self.jobrun_id = jobrun_id
        self.group = group
        self.name = name
        self.logger = logging.getLogger(logger_name)
        self.jobfile_dir = os.path.join(current_app.instance_path,
                                        'jobruns', group, name, str(jobrun_id))
        os.makedirs(self.jobfile_dir)


class JobInput(ParameterBase):
    pass


def _make_callback_wrapper(name, cparam):
    def callback(ctx, param, value):
        if value is None:
            return
        if param != cparam.name:
            return
        value = cparam.callback(ctx, cparam.name, value)
        setattr(ctx, name, value)
    return callback


class Job(WidgetBase):
    def __init__(self, **kw):
        assert kw.get('name') is None
        namespace, name = kw['namespace'].rsplit('.', 1)
        kw['namespace'] = namespace
        kw['name'] = name
        super(Job, self).__init__(**kw)
        module = inspect.getmodule(kw['callback'])
        self.version = '.'.join(['{0:04x}'.format(int(x))
                                 for x in module.__version__.split('.')])
        self.configs = [x for x in self.params if isinstance(x, Config)]
        self.inputs = [x for x in self.params if isinstance(x, JobInput)]

    def __call__(self, jobrun_id, **kw):
        assert _job_ctx_stack.top is None
        _job_ctx_stack.push(JobContext(jobrun_id=jobrun_id,
                                       group=self.namespace, name=self.name))
        cfg = {k: v for k, v in kw.items() if k != 'messages'}
        fileset = Jobrun.query.filter_by(id=jobrun_id).first().fileset
        return cfg, self.callback(fileset, **kw)

    # for cli integration
    @property
    def __name__(self):
        return self.name


def make_job_file(name):
    """Create a file associated with the current job"""
    # associate with jobrun
    jobctx = _job_ctx_stack.top
    jobrun = Jobrun.query.filter(Jobrun.id == jobctx.jobrun_id).first()
    jobfile = Jobfile(name=name, jobrun=jobrun)
    path = os.path.join(jobctx.jobfile_dir, name)
    assert not os.path.exists(path)  # just a precaution, not a race-safe check
    open(path, 'w').close()
    db.session.add(jobfile)
    db.session.commit()
    return path
