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

import click
import os
from .site import Site


@click.group()
def marv():
    pass


@marv.command()
@click.argument('directory', default=os.getcwd(),
                type=click.Path(file_okay=False, resolve_path=True))
def init(directory):
    """Create a Marv site or reinitialize an existing one"""
    site = Site.find_site(directory)
    if not site:
        site = Site(directory)
    site.init_root()


def cli():
    # from ipdb import launch_ipdb_on_exception
    # with launch_ipdb_on_exception():
    #     bagbunker(auto_envvar_prefix='MARV')
    marv(auto_envvar_prefix='MARV')


if __name__ == '__main__':
    cli()
