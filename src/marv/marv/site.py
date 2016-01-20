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
import logging
import os
import shutil
from pkg_resources import iter_entry_points, resource_filename, resource_stream

log = logging.getLogger(__name__)


INDEX_TEMPLATE = """\
<div class="container apps">
    <div class="row">
ROWS
    </div>
</div>
"""


ROW_TEMPLATE = """\
        <div class="col-xs-6">
            {{#link-to 'NAME'}}
                <img class="img-responsive img-rounded" src="app/styles/images/NAME.jpg">
            {{/link-to}}
            {{#link-to 'NAME' class="btn btn-default btn-block"}}NAME{{/link-to}}
        </div>\
"""


INDEX_HTML="""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <title>Marv</title>

    <base href="/" />

  </head>
  <body>
    <p>The frontend has not been built</p>
  </body>
</html>
"""


class Site(object):
    """A Marv site"""
    def __init__(self, root):
        assert root[0] == os.sep
        self.root = root
        """Absolute path to site root"""
        self.marv_dir = os.path.join(root, '.marv')
        """Absolute path to .marv dir usually within site root"""
        self.remotes_dir = os.path.join(self.marv_dir, 'remotes')
        """Remotes dir usually within marv_dir"""
        self.frontend = os.path.join(self.root, 'frontend')
        """Absolute path to site frontend folder"""
        self.frontend_dist = os.path.join(self.frontend, 'dist')
        """Absolute path to site frontend dist folder"""
        self.bejson = os.path.join(self.frontend, 'be.json')
        """Absolute path to generated be.json"""
        self.template_hbs = os.path.join(self.frontend, 'app', 'pods', 'index', 'template.hbs')
        """Absolute path to generated index/template.hbs"""
        self.marv_frontend = resource_filename('marv', 'frontend')
        """Absolute path to vanilla marv frontend folder"""

    @classmethod
    def find_site(cls, directory):
        """Look for site in directory and its parents"""
        assert directory[0] == os.sep
        while directory != os.sep:
            if os.path.exists(os.path.join(directory, '.marv')):
                return cls(directory)
            directory = os.path.dirname(directory)
        return None

    def init_root(self, symlink_frontend=None):
        root = self.root

        for directory in (root,  # explicitly create root dir
                          self.marv_dir,
                          self.remotes_dir):
            if not os.path.exists(directory):
                log.debug('Creating directory %s', directory)
                os.makedirs(directory)

        warning = os.path.join(root, 'FOR_NOW_MANUAL_CHANGES_WILL_BE_OVERWRITTEN')
        if not os.path.exists(warning):
            open(warning, 'wb').close()

        if symlink_frontend:
            if not os.path.islink(self.frontend):
                os.symlink(symlink_frontend, self.frontend)
        else:
            if os.path.islink(self.frontend):
                os.unlink(self.frontend)
            self.init_frontend()

        alembic_ini = resource_stream('marv', 'alembic.ini.in').read()
        alembic_ini = alembic_ini.replace('ALEMBIC_LOCATION',
                                          resource_filename('marv', 'alembic'))
        with open(os.path.join(root, 'alembic.ini'), 'wb') as f:
            f.write(alembic_ini)

        shutil.copy(resource_filename('marv', 'matplotlibrc.in'),
                    os.path.join(root, 'matplotlibrc'))

        shutil.copy(resource_filename('marv', 'bb.wsgi.in'),
                    os.path.join(root, 'bb.wsgi'))

        venv = os.environ['MARV_VENV']
        assert venv
        venv_link = os.path.join(root, 'venv')
        if not os.path.islink(venv_link):
            os.symlink(venv, venv_link)

        # remove old storage folder and .uuid file
        uuidfile = os.path.join(root, 'storage', '.uuid')
        if os.path.exists(uuidfile):
            os.unlink(uuidfile)
        if os.path.exists(os.path.dirname(uuidfile)):
            os.rmdir(os.path.dirname(uuidfile))

    def init_frontend(self):
        for directory in (self.frontend_dist,
                          os.path.dirname(self.bejson),
                          os.path.dirname(self.template_hbs)):
            if not os.path.exists(directory):
                log.debug('Creating directory %s', directory)
                os.makedirs(directory)

        index_html = os.path.join(self.frontend_dist, 'index.html')
        if not os.path.exists(index_html):
            with open(index_html, 'wb') as f:
                f.write(INDEX_HTML)

        shutil.copy(os.path.join(self.marv_frontend, 'bower.json.in'),
                    os.path.join(self.frontend, 'bower.json'))

        apps = []
        overlays = [self.marv_frontend]
        stylefiles = ['main.scss']
        for ep in iter_entry_points(group='marv_frontends'):
            apps.append(ep.name)
            pkg = ep.load()
            overlays.append(resource_filename(pkg.__name__, 'frontend'))
            stylefiles.append('{}.scss'.format(ep.name))

        bejson = resource_stream('marv', 'frontend/be.json.in').read()
        bejson = bejson.replace('OVERLAYS', json.dumps(overlays))
        bejson = bejson.replace('STYLEFILES', json.dumps(stylefiles))
        with open(self.bejson, 'wb') as f:
            f.write(bejson)

        template_hbs = INDEX_TEMPLATE.replace('ROWS', '\n'.join([
            ROW_TEMPLATE.replace('NAME', x) for x in apps
        ]))
        with open(self.template_hbs, 'wb') as f:
            f.write(template_hbs)
