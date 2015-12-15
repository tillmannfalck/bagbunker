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

import collections
import re

from .widget import _BaseWidget
from ._utils import title_from_name


FILTER = collections.OrderedDict()
COMPARISONS = {
    '==': lambda f, a: f == a,
    '!=': lambda f, a: f != a,
    '>': lambda f, a: f > a,
    '<': lambda f, a: f < a,
    '>=': lambda f, a: f >= a,
    '<=': lambda f, a: f <= a
}
comparisons = COMPARISONS.keys()
COMPARISON_OPS = comparisons


def compare(field, op, value):
    return COMPARISONS[op](field, value)


def filter_config():
    return [x.render() for x in FILTER.values()]


ValOp = collections.namedtuple('ValOp', ['val', 'op'])


size_re = re.compile('^\s*([0-9.]+)\s*([bkmgtpezy]b?)?\s*$', re.I)
units = 'bkmgtpezy'


def filesize(string):
    val, unit = size_re.match(string).groups()
    val = float(val)
    if unit:
        val *= 2**(10*units.index(unit.lower()[0]))
    return int(val)


NORMALIZATIONS = {
    'date': lambda x: x,
    'filesize': filesize,
    'float': lambda x: float(x),
    'integer': lambda x: int(x),
    'string': lambda x: str(x),
    'sublist': lambda x: x,
}


def normalize_input(value_type, value):
    fn = NORMALIZATIONS[value_type]
    if isinstance(value, list):
        value = [fn(v) for v in value]
    else:
        value = fn(value)
    return value


def filter_query(query, filters):
    unflattened = collections.defaultdict(dict)

    for k, v, in filters.items():
        filter_key, input_name = k.rsplit('::', 1)
        unflattened[filter_key][input_name] = v

    for key, filter in FILTER.items():
        inputs = unflattened.get(key)
        if inputs:
            for k, v in inputs.items():
                vtype = [i for i in filter.inputs if i.name == k][0].value_type
                inputs[k] = ValOp(normalize_input(vtype, v['val']), v['op'])
            query = filter(query, **inputs)

    return query


class Filter(_BaseWidget):
    """Filter widget and query
    """
    def __init__(self, **kw):
        super(Filter, self).__init__(**kw)
        self.inputs = [x for x in self.params if isinstance(x, FilterInput)]
        assert len(self.params) == len(self.inputs)

    def render(self):
        dct = super(Filter, self).render()
        dct.update({
            'inputs': [self._add_key(x.render()) for x in self.inputs]
        })
        return dct

    def _add_key(self, dct):
        dct['key'] = '::'.join([self.key, dct['name']])
        return dct

    def __call__(self, query, **inputs):
        return self.callback(query, **inputs)


class FilterInput(object):
    def __init__(self, name, operators, title=None, value_type='string',
                 constraints=None):
        self.name = name
        self.title = title_from_name(name) if title is None else title
        self.operators = operators
        self.value_type = value_type
        self.contraints = constraints

    def render(self):
        if callable(self.contraints):
            constraints = self.contraints()
        else:
            constraints = self.contraints

        return {
            'name': self.name,
            'title': self.title,
            'operators': self.operators,
            'value_type': self.value_type,
            'constraints': constraints
        }
