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

import click
import logging
from collections import OrderedDict
from functools import partial


LOGLEVEL_MAP = OrderedDict((
    # ('critical', 50),
    ('error', 40),
    ('warn', 30),
    ('info', 20),
    ('debug', 10),
))
LOGLEVELS = LOGLEVEL_MAP.keys()


def set_loglevel(ctx, p, v):
    if v is None:
        v = 'info'
    level = LOGLEVEL_MAP[v]
    logging.getLogger().setLevel(level)
    return v


loglevel_option = partial(click.option, '--loglevel',
                          type=click.Choice(LOGLEVELS),
                          default='info',
                          callback=lambda ctx, param, value: LOGLEVEL_MAP[value])
