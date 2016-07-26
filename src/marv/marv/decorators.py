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
from flask.ext.sqlalchemy import _BoundDeclarativeMeta as model_metaclass

from .job import MODELS
from .model import db
from .filtering import FILTER, Filter, FilterInput
from .listing import ListingColumn
from .registry import MODULE_NAME_MAP
from .serializer import Detail, Summary
from .serializer import DETAIL, SUMMARY
from .widget import Column, Image, Gallery, OSM, Row, Text, Table, Widget


def fileset():
    """Filesets are not namespaced"""
    def decorator(cls):
        name = cls.__name__
        tablename = re.sub('([A-Z])', lambda x: '_{}'.format(x.group(1).lower()),
                           name)[1:]
        bases = (db.Model,)
        class_dict = {
            '__doc__': cls.__doc__,
            '__module__': cls.__module__,
            '__tablename__': tablename,
            'id': db.Column(
                db.Integer, db.ForeignKey('fileset.id'),
                primary_key=True
            ),
            'fileset': db.relationship(
                'Fileset', uselist=False,
                backref=db.backref(tablename, uselist=False)
            ),
        }
        class_dict.update((k, v) for k, v in cls.__dict__.items()
                          if k[0] != '_')
        Model = model_metaclass(name, bases, class_dict)
        MODELS.append(Model)
        return Model
    return decorator


def _model_to_dict(self):
    return {
        'tablename': self.__tablename__,
        'data': {c.name: getattr(self, c.name)
                 for c in self.__table__.columns
                 if getattr(self, c.name) is not None}
    }


def job_model():
    def decorator(cls):
        name = cls.__name__
        package, jobname = cls.__module__.rsplit('.', 1)
        group = MODULE_NAME_MAP['job'][package]
        tablename = '__'.join([
            group,
            jobname,
            re.sub('([A-Z])', lambda x: '_{}'.format(x.group(1).lower()), name)[1:]
        ])
        bases = (db.Model,)
        class_dict = {
            '__doc__': cls.__doc__,
            '__module__': cls.__module__,
            '__tablename__': tablename,
            'id': db.Column(db.Integer, primary_key=True),
            'jobrun_id': db.Column(db.Integer, db.ForeignKey('jobrun.id')),
            'jobrun': db.relationship(
                'Jobrun', uselist=False,
                backref=db.backref(tablename, uselist=True)
            ),
            'as_dict': property(_model_to_dict)
        }
        class_dict.update((k, v) for k, v in cls.__dict__.items()
                          if k[0] != '_')
        Model = model_metaclass(name, bases, class_dict)
        MODELS.append(Model)
        return Model
    return decorator


#
# register callbacks/widgets for specific views
#

def detail(namespace=None, name=None, cls=Detail, **kw):
    """Register widget as detail serializer"""
    def decorator(widget):
        serializer = cls(namespace, name, widget, **kw)
        DETAIL.append(serializer)
        return serializer
    return decorator


def summary(namespace=None, name=None, cls=Summary, **kw):
    """Register widget as summary serializer"""
    def decorator(widget):
        serializer = cls(namespace, name, widget, **kw)
        SUMMARY.append(serializer)
        return serializer
    return decorator


#
# This is the newest, wait for jobs before cleanup
#
def filter(namespace=None, name=None, **kw):
    """Turn callback into query filter and widget"""
    def decorator(f):
        widget = filter_widget(name, namespace=namespace, **kw)(f)
        FILTER[widget.key] = widget
        return widget
    return decorator


#
# Widgets
#

# Heavily inspired by click.decorators._make_command
def _make_widget(f, name, cls, kw):
    if isinstance(f, Widget):
        raise TypeError('Attempted to convert a callback into a '
                        'renderer twice.')
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
    return cls(name=name or f.__name__.lower(),
               callback=f, params=params, **kw)


def image_widget(name=None, cls=Image, **kw):
    def decorator(f):
        return _make_widget(f, name, cls, kw)
    return decorator


def gallery_widget(name=None, cls=Gallery, **kw):
    def decorator(f):
        return _make_widget(f, name, cls, kw)
    return decorator


def filter_widget(name=None, cls=Filter, **kw):
    def decorator(f):
        return _make_widget(f, name, cls, kw)
    return decorator


def osm_widget(name=None, cls=OSM, **kw):
    def decorator(f):
        return _make_widget(f, name, cls, kw)
    return decorator


def row_widget(name=None, cls=Row, **kw):
    def decorator(f):
        return _make_widget(f, name, cls, kw)
    return decorator


def table_widget(name=None, cls=Table, **kw):
    def decorator(f):
        return _make_widget(f, name, cls, kw)
    return decorator


def text_widget(name=None, cls=Text, **kw):
    def decorator(f):
        return _make_widget(f, name, cls, kw)
    return decorator


#
# Paramaters
#

# Heavily inspired by click.decorators._param_memo
def _param_memo(f, param):
    if isinstance(f, Widget):
        f.params.append(param)
    else:
        if not hasattr(f, '__marv_params__'):
            f.__marv_params__ = []
        f.__marv_params__.append(param)


def column(*args, **kw):
    def decorator(f):
        if 'help' in kw:
            kw['help'] = inspect.cleandoc(kw['help'])
        cls = kw.pop('cls', Column)
        _param_memo(f, cls(*args, **kw))
        return f
    return decorator


def listing_column(*args, **kw):
    def decorator(f):
        if 'help' in kw:
            kw['help'] = inspect.cleandoc(kw['help'])
        cls = kw.pop('cls', ListingColumn)
        _param_memo(f, cls(*args, **kw))
        return f
    return decorator


def filter_input(*args, **kw):
    def decorator(f):
        if 'help' in kw:
            kw['help'] = inspect.cleandoc(kw['help'])
        cls = kw.pop('cls', FilterInput)
        _param_memo(f, cls(*args, **kw))
        return f
    return decorator
