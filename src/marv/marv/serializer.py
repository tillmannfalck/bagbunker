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
from flask_restless.serialization import DefaultSerializer


DETAIL = []
LISTING = []
SUMMARY = []
logger = logging.getLogger(__name__)


class Base(object):
    def __init__(self, namespace, name, widget, state=None):
        self.namespace = inspect.getmodule(widget.callback).__name__ \
            if namespace is None else namespace
        self.name = name
        self.widget = widget
        self.widget.state = state

    def __call__(self, fileset):
        try:
            return self.widget(fileset=fileset)
        except:
            import traceback
            logger.error(traceback.format_exc())


class Summary(Base):
    pass


class Detail(Base):
    pass


def fileset_detail(fileset, only=None):
    return {
        'id': fileset.id,
        'type': fileset.type,
        'name': fileset.name,
        'storage_id': fileset.storage_id,
        'comments': [{'author': {'username': x.author.username},
                      'text': x.text,
                      'timestamp': x.timestamp}
                     for x in fileset.comments],
        'tags': [{'id': x.id, 'label': x.label}
                 for x in fileset.tags],
        'widgets': filter(None, [proxy(fileset) for proxy in DETAIL])
    }


def fileset_summary(filesets):
    if not filesets.count():
        return {'widgets': []}

    return {
        'widgets': [proxy(filesets) for proxy in SUMMARY]
    }


def make_serializer(Model):
    # XXX ?
    only = getattr(Model, '__serialize_only__', None)
    exclude = getattr(Model, '__serialize_exclude__', None)
    additional = getattr(Model, '__serialize_additional__', [])
    additional += [x[0] for x in inspect.getmembers(Model)
                   if isinstance(x[1], serialized_property)]
    return DefaultSerializer(only=only, exclude=exclude,
                             additional_attributes=additional or None)


class serialized_property(property):
    pass
