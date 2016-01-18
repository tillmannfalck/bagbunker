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
import logging
import os
from .remotes import Remotes
from .site import Site


@click.group()
@click.option('--site-dir', type=click.Path(file_okay=False, resolve_path=True))
@click.pass_context
def marv(ctx, site_dir):
    """Manage a Marv site"""
    if site_dir:
        site = Site(site_dir)
    else:
        site = Site.find_site(os.getcwd())
    ctx.obj = site


@marv.command()
@click.option('--symlink-frontend', help="Symlink an existing frontend folder instead of creating a custom one")
@click.argument('directory', type=click.Path(file_okay=False, resolve_path=True))
def init(symlink_frontend, directory):
    """Create a Marv site or reinitialize an existing one"""
    if directory:
        site = Site(directory)
    else:
        site = Site.find_site(os.getcwd())
    site.init_root(symlink_frontend=symlink_frontend)


@marv.group(invoke_without_command=True)
@click.option('-v', '--verbose', is_flag=True)
@click.pass_context
def remote(ctx, verbose):
    """Managed set of remote instances"""
    site = ctx.obj
    remotes = Remotes(site)
    for name, remote in sorted(remotes.items()):
        if verbose:
            click.echo('{} {}'.format(name, remote.url))
        else:
            click.echo(remote.name)
    ctx.obj = remotes


@remote.command()
@click.argument('name', required=True)
@click.argument('url', required=True)
@click.pass_obj
def add(remotes, name, url):
    """Add remote instance"""
    remotes.add(name, url)


@remote.command()
@click.argument('name', required=True)
@click.pass_obj
def rm(remotes, name):
    """Remove remote instance"""
    remotes.rm(name)


@remote.command()
@click.argument('name')
@click.pass_obj
def update(remotes, name):
    """Update fileset listing for remote, all remotes if name not given."""
    if name:
        remotes.update(name)
    else:
        remotes.update_all()


def cli():
    # setup global logging - see also @log.verbose on commands
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)

    # from ipdb import launch_ipdb_on_exception
    # with launch_ipdb_on_exception():
    #     bagbunker(auto_envvar_prefix='MARV')
    marv(auto_envvar_prefix='MARV')


if __name__ == '__main__':
    cli()
