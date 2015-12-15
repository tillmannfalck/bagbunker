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

import os
import flask.ext.sqlalchemy
from datetime import datetime


db = flask.ext.sqlalchemy.SQLAlchemy()


class Storage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, index=True)
    filesets = db.relationship('Fileset', backref=db.backref('storage', uselist=False),
                               cascade='save-update, delete, delete-orphan, merge')


class Fileset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'), nullable=False)
    md5 = db.Column(db.String(32), index=True, nullable=False)
    name = db.Column(db.String(126), nullable=False)
    dirpath = db.Column(db.String, nullable=False)
    files = db.relationship('File', backref=db.backref('fileset', uselist=False),
                            cascade='save-update, delete, delete-orphan, merge')
    deleted = db.Column(db.Boolean)
    deleted_reason = db.Column(db.String(126))
    type = db.Column(db.String(32), nullable=False)
    time_added = db.Column(db.TIMESTAMP, nullable=False)
    time_updated = db.Column(db.TIMESTAMP, nullable=False)
    time_read = db.Column(db.TIMESTAMP)
    read_succeeded = db.Column(db.Boolean)
    read_error = db.Column(db.String)

    def update_from(self, other):
        changed_attrs = []
        for attr in ('name', 'dirpath', 'type'):
            value = getattr(other, attr)
            if getattr(self, attr) != value:
                changed_attrs.append(attr)
                setattr(self, attr, value)
        if changed_attrs:
            files = list(self.files)
            for x in files:
                self.files.remove(x)
            db.session.flush()
            for x in other.files:
                self.files.append(File.from_file(x))
            self.time_updated = datetime.utcnow()
        return changed_attrs

    def __repr__(self):
        return '<{} "{}" type="{}" dir="{}" files={} md5="{}">'.format(
            self.__class__.__name__,
            self.name, self.type, self.dirpath, len(self.files), self.md5)

    @property
    def broken(self):
        return any(x.missing for x in self.files)

    @property
    def failed_job_names(self):
        # check latest jobruns for failed flag and list them
        jobs = {}
        for jobrun in self.jobruns:
            if jobrun.id > jobs.setdefault(jobrun.name, jobrun).id:
                jobs[jobrun.name] = jobrun

        return [name for name in sorted(
            job.name for job in jobs.values() if job.failed)]

    # XXX: latest_jobrun like current_app
    def get_latest_jobrun(self, name):
        jobrun = Jobrun.query.filter(Jobrun.fileset_id == self.id)\
                             .filter(Jobrun.name == name) \
                             .order_by(Jobrun.id.desc()).first()
        return jobrun


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileset_id = db.Column(db.Integer, db.ForeignKey('fileset.id'), nullable=False)
    md5 = db.Column(db.String(32), index=True, nullable=False)
    missing = db.Column(db.Boolean)
    name = db.Column(db.String(126), nullable=False)
    size = db.Column(db.BigInteger, nullable=False)

    @property
    def path(self):
        return os.path.join(self.fileset.dirpath, self.name)

    @classmethod
    def from_file(cls, other):
        return cls(md5=other.md5, name=other.name, size=other.size)

    def __repr__(self):
        return '<{} "{}" md5="{}" size={}>'.format(
            self.__class__.__name__,
            self.name, self.md5, self.size)


fileset_tags = db.Table(
    'fileset_tags',
    db.Column('fileset_id', db.Integer, db.ForeignKey('fileset.id'), nullable=False),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), nullable=False)
)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filesets = db.relationship('Fileset', secondary=fileset_tags,
                               backref=db.backref('tags'))
    label = db.Column(db.String(126), unique=True, index=True)


class Comment(db.Model):
    """A comment can optionally be made to a specific field (<table>.<field>)
    """
    id = db.Column(db.Integer, primary_key=True)
    fileset = db.relationship('Fileset', uselist=False,
                              backref=db.backref('comments'))
    fileset_id = db.Column(db.Integer, db.ForeignKey('fileset.id'), nullable=False)
    author = db.relationship('User', uselist=False, backref=db.backref('comments'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text)
    timestamp = db.Column(db.TIMESTAMP(timezone=True), default=db.func.now())


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(126), unique=True, index=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)


class Jobrun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileset = db.relationship('Fileset', uselist=False, backref=db.backref('jobruns'))
    fileset_id = db.Column(db.Integer, db.ForeignKey('fileset.id'), nullable=False)
    name = db.Column(db.String(126), nullable=False)
    version = db.Column(db.String(14), nullable=False)
    config = db.Column(db.String)  # json serialised job config
    failed = db.Column(db.Boolean)
    succeeded = db.Column(db.Boolean)


class Jobfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(126))
    jobrun = db.relationship('Jobrun', uselist=False, backref=db.backref('jobfiles'))
    jobrun_id = db.Column(db.Integer, db.ForeignKey('jobrun.id'), nullable=False)


# class Listing(db.Model):
#     __bind_key__ = 'cachedb'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String)
#     md5 = db.Column(db.String)
#     size = db.Column(db.Integer)
#     tags = db.Column(db.String)
#     status = db.Column(db.String)
#     file_count = db.Column(db.Integer)
#     job_count = db.Column(db.Integer)
#     comment_count = db.Column(db.Integer)
