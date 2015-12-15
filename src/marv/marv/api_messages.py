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

import flask
from .model import Fileset, File, db
from .registry import READER

api = flask.Blueprint('api_message', __name__)


class NoMatchingMimetype(Exception):
    pass


@api.route('/api/messages/<md5>')
def messages(md5):
    # XXX: limit to storage we are running in
    fileset = Fileset.query.join(File)\
                           .options(db.contains_eager(Fileset.files))\
                           .filter(Fileset.md5 == md5 and
                                   Fileset.deleted.isnot(True) and
                                   ~Fileset.file.any(File.missing.is_(True)))\
                           .first_or_404()

    reader = READER[fileset.type]
    try:
        generator = reader.http_messages
    except AttributeError:
        flask.abort(400, 'Fileset does not support streaming')

    request = flask.request
    accept_mimetypes = request.accept_mimetypes
    kw = dict(request.args.iterlists())
    try:
        messages, mimetype = \
            generator(fileset, accept_mimetypes=accept_mimetypes, **kw)
    except NoMatchingMimetype:
        flask.abort(400, 'No matching mimetype %s' % accept_mimetypes)
    return flask.Response(flask.stream_with_context(messages), mimetype=mimetype)
