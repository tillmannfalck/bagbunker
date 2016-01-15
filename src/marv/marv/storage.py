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
from datetime import datetime
from itertools import chain
from logging import getLogger
from uuid import uuid4
from . import queries
from .model import db, Fileset
from .model import Storage as _Storage
from .reader import READER
from .scanner import SCANNER, scan


class Storage(object):
    def __init__(self, reader=None, scanner=None):
        self.reader = READER if reader is None else reader
        self.scanner = SCANNER if scanner is None else scanner
        # XXX: we probably can get rid of model.Storage as we do not
        # need it for sync anymore
        storages = _Storage.query.all()
        assert len(storages) <= 1
        if storages:
            self.instance = storages[0]
        else:
            raise ValueError('No storage defined')

    @classmethod
    def new_storage(cls, reader=None, scanner=None):
        uuid = str(uuid4())
        db.session.add(_Storage(uuid=uuid))
        db.session.commit()
        return cls(reader=reader, scanner=scanner)

    @property
    def filesets(self):
        return Fileset.query.filter(Fileset.storage_id == self.instance.id)

    # XXX: do we need these here?

    @property
    def active_filesets(self):
        return queries.active_filesets(self.filesets)

    @property
    def active_intact_filesets(self):
        return queries.active_intact_filesets(self.filesets)

    @property
    def broken_filesets(self):
        return queries.broken_filesets(self.filesets)

    @property
    def pending_filesets(self):
        return queries.pending_filesets(self.filesets)

    @property
    def uuid(self):
        return self.instance.uuid

    def _detect_missing(self, logger):
        """Detect missing files for active filesets"""
        for fileset in self.active_filesets:
            for file in fileset.files:
                missing = not os.path.exists(file.path)
                if missing ^ (file.missing or False):
                    if missing:
                        logger.warn('Lost file %r of %r', file, fileset)
                    else:
                        logger.info('Found missing file %r of %r', file, fileset)
                    file.missing = missing
        db.session.commit()

    def read_pending(self, logger=getLogger(__name__)):
        reader = self.reader
        for fileset in self.pending_filesets:
            try:
                logger.info('reading %r', fileset)
                instance = reader[fileset.type].read(fileset)
                # # XXX: this is probably non-functional
                # existing = getattr(fileset, fileset.type, None)
                # if existing is not None:
                #     db.session.delete(existing)
                #     db.session.flush()
                setattr(fileset, fileset.type, instance)
                fileset.time_read = datetime.utcnow()
                fileset.read_succeeded = True
                db.session.commit()
                logger.debug('read %r', fileset)
            except Exception as e:
                import traceback
                logger.error('skipped %r due to exception\n%s',
                             fileset, traceback.format_exc())
                db.session.rollback()
                fileset.time_read = datetime.utcnow()
                fileset.read_succeeded = False
                fileset.read_error = unicode(e) or 'unknown'
                db.session.commit()

    def scan(self, basedir):
        return self.scan_all((basedir,))

    def scan_all(self, basedirs, logger=getLogger(__name__)):
        seen = set()
        for found in chain.from_iterable(scan(x, self.scanner) for x in basedirs):
            try:
                active = self.active_filesets.filter_by(md5=found.md5).first()
                if active is None:
                    # New, duplicate, or superseding fileset
                    active = self.active_filesets \
                        .filter((Fileset.name == found.name) &
                                (Fileset.type == found.type)).first()

                    # New fileset?
                    if active is None:
                        self.instance.filesets.append(found)
                        db.session.commit()
                        logger.info('added new %r', found)
                        seen.add(found.md5)
                        continue

                    # Duplicate?
                    if active.files[0].path != found.files[0].path and \
                       os.path.exists(active.files[0].path) and \
                       os.path.exists(found.files[0].path):
                        logger.warn('skipped duplicate %r keeping %r', found, active)
                        continue

                    # superseding
                    active.deleted = True
                    active.deleted_reason = '__superseded__'
                    self.instance.filesets.append(found)
                    db.session.commit()
                    logger.info('%r superseds %r', found, active)
                    seen.add(found.md5)
                    continue

                # Duplicate?
                if active.files[0].path != found.files[0].path and \
                   os.path.exists(active.files[0].path) and \
                   os.path.exists(found.files[0].path):
                    logger.warn('skipped duplicate %r keeping %r', found, active)
                    continue

                changed_attrs = active.update_from(found)
                if changed_attrs:
                    db.session.commit()
                    logger.info('updated %s: %s', ', '.join(changed_attrs), active)
                seen.add(found.md5)
            except:
                import traceback
                logger.error('skipped %r due to exception\n%s',
                             found, traceback.format_exc())
                db.session.rollback()
        self._detect_missing(logger)
