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
import re
from collections import OrderedDict


from ._utils import title_from_name


class _BaseWidget(object):
    name = None
    namespace = None   # often set after instantiation
    type = None
    state = None       # currently set from outside

    def __init__(self, name, callback, params, namespace=None,
                 title=None, help=None, type=None):
        self.name = name
        self.callback = callback
        self.params = params
        self.namespace = inspect.getmodule(callback).__name__ \
            if namespace is None else namespace
        self.title = title_from_name(name) if title is None else title
        self.help = help
        self.type = type \
            if type is not None \
            else self.__class__.__name__.lower()

    @property
    def key(self):
        return '::'.join([self.namespace, self.name])

    def render(self):
        return {
            'name': self.name,
            'namespace': self.namespace,
            'title': self.title,
            'type': self.type,
            # 'key': self.key,
        }


class Column(object):
    def __init__(self, name, title=None, formatter='string', list=None):
        self.name = name
        self.title = title \
            if title is not None \
            else re.sub('(\A|_)(.)',
                        lambda m: (m.group(1) and ' ') + m.group(2).upper(), name)
        self.formatter = formatter
        self.list = list

    def __call__(self, dct):
        self.value = dct.get(self.name, None)
        keys = ('name', 'title', 'formatter', 'list', 'value')
        values = (getattr(self, x) for x in keys)
        rv = dict((
            k,
            v if self.list else ' '.join(v) if type(v) in (tuple, list) else v
        ) for k, v in zip(keys, values) if v is not None)
        del self.value
        return rv


class Widget(object):
    def __init__(self, name, callback, params, title=None, help=None, type=None):
        self.name = name
        self.title = title \
            if title is not None \
            else re.sub('(\A|_)(.)',
                        lambda m: (m.group(1) and ' ') + m.group(2).upper(), name)
        self.type = type \
            if type is not None \
            else self.__class__.__name__.lower()
        self.callback = callback
        self.help = help
        self.all_params = params
        self.entities = OrderedDict()
        self.columns = []
        for x in params:
            if isinstance(x, Column):
                self.columns.append(x)

    def __call__(self, fileset):
        values = self.callback(fileset)
        if values is None:
            return None
        dct = {
            'title': self.title,
            'state': self.state,
            'type': self.type,
            # 'headerText': '',
            # 'footerText': 'Footer XXX',
            # 'job': 'Job XXX',
        }
        return self.serialize(dct, values)


class Image(Widget):
    def serialize(self, dct, image):
        dct.update({
            'image': image
        })
        return dct


class Gallery(Widget):
    def serialize(self, dct, images):
        dct.update({
            'images': images
        })
        return dct


class Row(Widget):
    def serialize(self, dct, row):
        dct.update({
            'columns': [col(row) for col in self.columns],
        })
        return dct


class Table(Widget):
    def __init__(self, sort=None, **kw):
        super(Table, self).__init__(**kw)
        self.sort = sort

    def serialize(self, dct, rows):
        dct.update({
            'sort': self.sort,
            'rows': [{'columns': [col(row) for col in self.columns]}
                     for row in rows]
        })
        return dct


class Text(Widget):
    def serialize(self, dct, text):
        dct.update({
            'text': text
        })
        return dct
