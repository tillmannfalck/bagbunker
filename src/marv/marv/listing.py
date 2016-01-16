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

import json
import re
import os
from collections import OrderedDict
from flask import current_app as app
from flask.ext.sqlalchemy import _BoundDeclarativeMeta as model_metaclass, inspect
from .model import db, Fileset
from ._utils import title_from_name


LISTING_CALLBACKS = OrderedDict()
ListingEntry = None
Relations = {}


def related_model(name):
    return Relations[name]


def related_field(name):
    return Relations[name].value


class ListingColumn(object):
    def __init__(self, name, title=None, formatter='string',
                 type=db.String, json=False, hidden=False, relation=False, list=False):
        self.name = name
        self.title = title \
            if title is not None \
            else re.sub('(\A|_)(.)',
                        lambda m: (m.group(1) and ' ') + m.group(2).upper(), name)
        self.formatter = formatter
        self.type = type
        self.json = json
        self.hidden = hidden
        self.relation = relation
        self.list = list


class ListingCallback(object):
    name = None
    namespace = None
    type = None

    @property
    def key(self):
        return '::'.join([self.namespace, self.name]) \
            if self.namespace else self.name

    def __init__(self, name, callback, params, namespace=None,
                 help=None, title=None, type=None):
        self.name = name or 'foo'
        self.namespace = namespace
        self.help = help
        self.type = type \
            if type is not None \
            else self.__class__.__name__.lower()
        self.callback = callback
        self.columns = []
        for x in params if params is not None else []:
            if isinstance(x, ListingColumn):
                self.columns.append(x)


def generate_listing_model():
    global ListingEntry, Relations
    name = 'ListingEntry'
    bases = (db.Model,)
    class_dict = {
        '__bind_key__': 'cache',
        '__tablename__': 'listing_entry',
        'id': db.Column(db.String, primary_key=True),  # md5
        'remote': db.Column(db.String),                # url
    }
    relcols = []
    for name, callback in LISTING_CALLBACKS.items():
        for col in callback.columns:
            assert col.name not in class_dict
            if col.relation:
                assert col.name not in Relations
                relcols.append(col)
            else:
                class_dict[col.name] = db.Column(col.type)
    ListingEntry = model_metaclass(name, bases, class_dict)
    for col in relcols:
        Relations[col.name] = generate_relation_model(col)
    db.create_all(bind='cache')
    return ListingEntry


def generate_relation_model(col):
    assert col.relation
    name = col.name
    bases = (db.Model,)
    class_dict = {
        '__bind_key__': 'cache',
        '__tablename__': col.name,
        'id': db.Column(db.Integer, primary_key=True),
        'listing_entry': db.relationship(
            ListingEntry, uselist=False,
            backref=db.backref(col.name,
                               cascade='save-update, delete, delete-orphan, merge')),
        'listing_entry_id': db.Column(db.Integer, db.ForeignKey('listing_entry.id')),
        'value': db.Column(col.type),
    }
    Relation = model_metaclass(name, bases, class_dict)
    return Relation


def update_listing_entry(fileset):
    entry_dict = {'id': fileset.md5, 'remote': None}
    for name, callback in LISTING_CALLBACKS.items():
        names = {x.name for x in callback.columns}
        dct = callback.callback(fileset)
        assert len(set(dct.keys()) - names) == 0
        for col in callback.columns:
            value = dct.get(col.name)
            if col.relation:
                if value is None:
                    value = []
                Relation = Relations[col.name]
                value = [Relation(value=x) for x in value]
            entry_dict[col.name] = value
    entry = ListingEntry(**entry_dict)
    db.session.add(entry)
    db.session.flush()


def populate_listing_cache():
    for fileset in Fileset.query.filter(Fileset.type == 'bag'):
        update_listing_entry(fileset)
    db.session.commit()

    remotepath = os.path.join(app.instance_path, 'remotes')
    for name in os.listdir(remotepath):
        load_remote_listing(name)


def serialize_listing_entry(entry):
    columns = [{
        'formatter': 'icon',
        'name': 'Location',
        'title': '',
        'value': {
            'icon': 'hdd',
            'title': 'Location: {}'.format(entry.remote or 'local'),
            'classes': 'text-warning' if entry.remote else 'text-success'
        }
    }]
    for callback in LISTING_CALLBACKS.values():
        for col in callback.columns:
            if not col.hidden:
                value = getattr(entry, col.name)
                if col.json:
                    value = json.loads(value)
                columns.append({
                    'formatter': col.formatter,
                    'name': col.name,
                    'list': col.list,
                    'title': col.title,
                    'value': value,
                })
    return {
        'id': entry.fid,
        'type': entry.type,
        'storage_id': entry.storage_id,
        'columns': columns,
    }


def get_local_listing():
    entries = ListingEntry.query.filter(ListingEntry.remote.is_(None))
    results = {}
    for entry in entries:
        results[entry.id] = result = {}
        for callback in LISTING_CALLBACKS.values():
            for col in callback.columns:
                value = getattr(entry, col.name)
                if col.relation:
                    value = [v.value for v in value]
                result[col.name] = value
    return results


def load_remote_listing(name):
    filename = os.path.join(app.instance_path, 'remotes', name)
    with open(filename, 'r') as f:
        data = json.load(f)
    ids = data.keys()

    outdated = (ListingEntry.query
                            .filter(ListingEntry.remote.isnot(None))
                            .filter(ListingEntry.id.in_(ids)))

    for o in outdated:
        db.session.delete(o)
    db.session.commit()

    local = [l.md5 for l in ListingEntry.query.filter(ListingEntry.id.in_(ids))]

    for id_, entry in data.items():
        if entry['md5'] not in local:
            for callback in LISTING_CALLBACKS.values():
                for col in callback.columns:
                    if col.relation:
                        entry[col.name] = [Relations[col.name](value=e)
                                           for e in entry[col.name]]
            db.session.add(ListingEntry(id=id_, remote=name, **entry))

    db.session.commit()
    return {}


def set_remote_listing(listing):
    for remote, data in listing.items():
        filename = os.path.join(app.instance_path, 'remotes', remote)
        with open(filename, 'w') as f:
            json.dump(data, f)
        load_remote_listing(remote)
    return {}
