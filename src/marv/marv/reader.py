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

from logging import getLogger
from .widgeting import make_register, WidgetBase


class Reader(WidgetBase):
    def __init__(self, **kw):
        kw['name'] = kw['name'].__tablename__
        super(Reader, self).__init__(**kw)

    def read(self, fileset):
        return self.callback(fileset)

    def http_messages_generator(self, generator):
        def http_messages(fileset, **kw):
            logger = getLogger('{}.messages.{}'.format(self.name, fileset.md5))
            return generator(fileset, logger=logger, **kw)
        self.http_messages = http_messages


READER = dict()
reader = make_register('reader', namespace='', registry=READER, cls=Reader)
