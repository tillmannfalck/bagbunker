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

from collections import OrderedDict
from .job import Job
from .listing import ListingCallback, LISTING_CALLBACKS
from .reader import READER, reader    # noqa  -- registry should be an instance
from .scanner import SCANNER, scanner    # noqa  -- registry should be an instance
from .widgeting import make_register, MODULE_NAME_MAP

JOB = OrderedDict()
job = make_register('job', registry=JOB, cls=Job)

listing = make_register('listing', registry=LISTING_CALLBACKS, cls=ListingCallback)


FORMATS_LOADED = False
JOBS_LOADED = False


def load_formats():
    global FORMATS_LOADED
    if FORMATS_LOADED:
        return
    import pkg_resources
    for ep in pkg_resources.iter_entry_points(group='marv_formats'):
        ep.load()
    FORMATS_LOADED = True


def load_jobs():
    global JOBS_LOADED
    if JOBS_LOADED:
        return
    import pkg_resources
    for ep in pkg_resources.iter_entry_points(group='marv_jobs'):
        MODULE_NAME_MAP.setdefault('job', {})[ep.module_name] = ep.name
        ep.load()
    JOBS_LOADED = True
