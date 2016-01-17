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
from ConfigParser import SafeConfigParser
from collections import namedtuple


Remote = namedtuple('Remote', ['name', 'path', 'url'])


class Remotes(object):
    """Manage a Marv site's remotes"""
    def __init__(self, site):
        self.site = site
        """Site for which to manage remotes"""

        self.path = os.path.join(site.marv_dir, 'remotes')
        """Path to remotes directory"""

    def __repr__(self):
        return '<Remotes {}>'.format(self.path)

    def __iter__(self):
        return iter(os.listdir(self.path))

    keys = __iter__

    # def values(self):
    #     return (Remote(name=name,
    #                    path=os.path.join(self.path, name),
    #                    url=
    #                    for name in os.listdir(self.path)))

    def items(self):
        return ((x.name, x) for x in self.values())

    def add(self, name, url):
        """Add a remote"""
        # Create directory
        # Write url into directory

    def rm(self, name):
        """Remove a remote"""

    def update(self, name):
        """Update a remote"""

    def update_all(self):
        """Update all remotes"""
