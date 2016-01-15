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
import pkg_resources


frontend = flask.Blueprint('frontend', __name__)


# ATTENTION: routes producing the same variables would trigger redirects,
# setting foo/bar is a hack to prevent this
@frontend.route('/', defaults={'path': 'index.html', 'foo': -1, 'bar': -1})
@frontend.route('/<path:path>', defaults={'foo': -2, 'bar': -2})
def frontend_routes(path, foo, bar):
    """Serve frontend - our static files"""
    return flask.send_from_directory(flask.current_app.config['FRONTEND_PATH'], path)


i = 0
for ep in pkg_resources.iter_entry_points(group='marv_frontends'):
    deco1 = frontend.route('/{}'.format(ep.name),
                           defaults={'path': 'index.html', 'foo': i, 'bar': i})
    i += 1
    deco2 = frontend.route('/{}/<path:foo>'.format(ep.name),
                           defaults={'path': 'index.html', 'bar': i})
    i += 1
    frontend_routes = deco1(frontend_routes)
    frontend_routes = deco2(frontend_routes)
