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
from ._utils import title_from_name


MODULE_NAME_MAP = {}


class KeyCollision(Exception):
    pass


class ParameterBase(object):
    name = None
    namespace = None
    type = None

    def __init__(self, name, namespace=None, title=None, help=None,
                 type=None):
        self.name = name
        self.namespace = namespace
        self.title = title_from_name(name) if title is None else title
        self.help = help
        self.type = type \
            if type is not None \
            else self.__class__.__name__.lower()

    def __call__(self, value):
        return value

    @property
    def key(self):
        return '::'.join([self.namespace, self.name]) \
            if self.namespace else self.name

    def render(self):
        return {
            'key': self.key,
            'name': self.name,
            'namespace': self.namespace,
            'title': self.title,
            'type': self.type,
            'help': self.help,
        }


class WidgetBase(ParameterBase):
    def __init__(self, callback, params=None, **kw):
        name = kw.get('name')
        kw['name'] = name if name is not None else callback.__name__.lower()
        super(WidgetBase, self).__init__(**kw)
        self.callback = callback
        self.params = params if params is not None else []


def make_register(register_name, registry, cls=None, namespace=None):
    def decorator_factory(name=None, namespace=namespace, cls=cls,
                          registry=registry, **kw):
        def decorator(f_or_widget):
            if cls:
                if namespace is None:
                    _namespace = inspect.getmodule(f_or_widget).__name__
                    for k, v in MODULE_NAME_MAP.get(register_name, {}).items():
                        if _namespace.startswith(k):
                            _namespace = _namespace.replace(k, v, 1)
                            break
                else:
                    _namespace = namespace
                widget = make_widget(f_or_widget, name=name,
                                     namespace=_namespace, cls=cls, kw=kw)
            else:
                widget = f_or_widget
            if widget.key in registry:
                raise KeyCollision(widget.key, widget)
            registry[widget.key] = widget
            return widget
        return decorator
    decorator_factory.__name__ = register_name
    return decorator_factory


# Heavily inspired by click.decorators._make_command
def make_widget(f, name, namespace, cls, kw):
    if isinstance(f, WidgetBase):
        raise TypeError('Attempted to convert a callback into a widget twice.')
    try:
        params = f.__marv_params__
        params.reverse()
        del f.__marv_params__
    except AttributeError:
        params = []
    help = kw.get('help')
    if help is None:
        help = inspect.getdoc(f)
        if isinstance(help, bytes):
            help = help.decode('utf-8')
    else:
        help = inspect.cleandoc(help)
    kw['help'] = help
    return cls(name=name, namespace=namespace, callback=f, params=params, **kw)


# Heavily inspired by click.decorators._param_memo
def _param_memo(f, param):
    if isinstance(f, WidgetBase):
        f.params.append(param)
    else:
        if not hasattr(f, '__marv_params__'):
            f.__marv_params__ = []
        f.__marv_params__.append(param)


def make_parameter(parameter_name, cls):
    def decorator_factory(name=None, **kw):
        name = name if name is not None else cls.__name__.lower()

        def decorator(f):
            if 'help' in kw:
                kw['help'] = inspect.cleandoc(kw['help'])
            _cls = kw.pop('cls', cls)
            _param_memo(f, _cls(name=name, **kw))
            return f
        return decorator
    decorator_factory.__name__ = parameter_name
    return decorator_factory
