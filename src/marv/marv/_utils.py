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
import json
import re
from Queue import Queue
from itertools import tee
from collections import namedtuple
from threading import Thread
from .globals import _job_ctx_stack
from .model import db, Jobrun


def multiplex(inputs, processors, logger=None, dont_catch=False):
    """tee inputs, feed to each processor and return multiplexed outputs"""
    generators = []
    zipped = zip(processors, tee(inputs, len(processors)))
    for processor, _inputs in zipped:
        if dont_catch:
            generator = processor(_inputs)
            assert inspect.isgenerator(generator)
        else:
            try:
                generator = processor(_inputs)
            except:
                import traceback
                if logger:
                    logger.error(traceback.format_exc())
                else:
                    traceback.print_exc()  # noqa #pragma nocoverage
                continue
        generators.append(generator)

    while generators:
        for outputs in generators:
            if dont_catch:
                try:
                    yield outputs.next()
                except StopIteration:
                    generators.remove(outputs)
                continue
            try:
                yield outputs.next()
            except StopIteration:
                generators.remove(outputs)
            except:
                import traceback
                if logger:
                    logger.error(traceback.format_exc())
                else:
                    traceback.print_exc()  # noqa #pragma nocoverage
                generators.remove(outputs)


def title_from_name(name):
    return re.sub('(\A|_)(.)',
                  lambda m: (m.group(1) and ' ') + m.group(2).upper(), name)


AsyncJob = namedtuple('AsyncJob', ['thread', 'msg_queue', 'rv_queue',
                                   'name', 'fileset_id', 'version',
                                   'jobrun_id', 'topics'])


class Done(object):
    pass
Done = Done()


class Failed(object):
    pass
Failed = Failed()


class EffectiveConfig(object):
    def __init__(self, cfg):
        self.cfg = cfg


def make_async_job(app, name, job, topics, group, version, config, fileset_id):
    if config is None:
        config = {}
    msg_queue = Queue()
    rv_queue = Queue()

    def messages():
        while True:
            x = msg_queue.get()
            if x is Done:
                msg_queue.task_done()
                break
            yield x
            msg_queue.task_done()

    def async_job(app, messages, jobrun_id):
        with app.app_context():
            try:
                db.create_all()
                cfg, rv_generator = \
                    job(jobrun_id=jobrun_id, messages=messages(), **config)
                rv_queue.put(EffectiveConfig(cfg))
                for rv in rv_generator:
                    rv_queue.put(rv)
            except:
                import traceback
                traceback.print_exc()
                rv_queue.put(Failed)
            finally:
                _job_ctx_stack.pop()
                rv_queue.put(Done)
                db.session.remove()

    jobrun = Jobrun(name=name, version=version, fileset_id=fileset_id)
    db.session.add(jobrun)
    db.session.commit()
    thread = Thread(target=async_job, name=name, args=(app, messages, jobrun.id))
    thread.daemon = True
    thread.start()

    return AsyncJob(thread=thread, msg_queue=msg_queue, topics=topics,
                    rv_queue=rv_queue, name=name, version=version,
                    fileset_id=fileset_id, jobrun_id=jobrun.id)


def async_job_milker(app, async_job):
    with app.app_context():
        db.create_all()
        jobrun = Jobrun.query.filter(Jobrun.id == async_job.jobrun_id).first()
        try:
            while True:
                res = async_job.rv_queue.get()
                if isinstance(res, EffectiveConfig):
                    jobrun.config = json.dumps(res.cfg)
                    continue
                if res is Done:
                    jobrun.succeeded = True
                    db.session.commit()
                    break
                if res is Failed:
                    jobrun.failed = True
                    db.session.commit()
                    break
                instance = res
                instance.jobrun = jobrun
                db.session.add(instance)
                db.session.commit()
        except:
            import traceback
            traceback.print_exc()  # noqa #pragma nocoverage
            jobrun.failed = True
            db.session.commit()
        finally:
            db.session.remove()
