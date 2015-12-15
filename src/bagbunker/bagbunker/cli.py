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

"""
With flask 1.0 this will be migrated to Flask.cli.

We already use click, which is used by Flask.cli as well.
"""

from __future__ import absolute_import, division

import click
import ConfigParser
import flask
import logging
import os
import shutil
from collections import OrderedDict
from functools import partial
from threading import Thread
from werkzeug import release_local
from marv import create_app, load_formats, load_jobs
from marv.globals import _job_ctx_stack
from marv.log import loglevel_option
from marv.model import db, Fileset, Jobfile, Jobrun
from marv.storage import Storage

from marv.registry import JOB
from marv._utils import make_async_job, async_job_milker, Done


load_formats()
load_jobs()


def config_option(key):
    def callback(ctx, param, value):
        ctx.params.setdefault('config', dict())[key] = value
        return value
    return callback


def read_config(path):
    parser = ConfigParser.RawConfigParser()
    parser.read([path])
    cfg = {}
    for section in parser.sections():
        seccfg = reduce(lambda acc, x: acc.setdefault(x, {}), section.split('.'), cfg)
        for key, value in parser.items(section):
            seccfg[key] = value
    return cfg


STORAGE = None
UUID_FILE = None


@click.group()
@loglevel_option()
@click.option('--instance-path', type=click.Path(resolve_path=True, file_okay=False),
              expose_value=False, callback=config_option('INSTANCE_PATH'))
@click.option('--debug/--no-debug', default=None,
              expose_value=False, callback=config_option('DEBUG'))
@click.option('--echo-sql/--no-echo-sql', default=None,
              expose_value=False, callback=config_option('SQLALCHEMY_ECHO'))
@click.option('--sqlite/--no-sqlite', callback=config_option('USE_SQLITE'),
              expose_value=False, default=None)
@click.pass_context
def bagbunker(ctx, config, loglevel):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(loglevel)
    logging.getLogger('rospy').setLevel(logging.WARNING)
    if config.get('DEBUG'):
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    ctx.obj = app = create_app('marv.settings.Development', **config)
    app_context = app.app_context()
    app_context.push()
    ctx.call_on_close(partial(release_local, _job_ctx_stack))

    global UUID_FILE, STORAGE
    UUID_FILE = os.path.join(app.instance_path, 'storage', '.uuid')
    try:
        with open(UUID_FILE, 'rb') as f:
            uuid = f.read(36)
        STORAGE = Storage(uuid=uuid)
    except:
        db.session.rollback()

    @ctx.call_on_close
    def closedb():
        db.session.close()


ALEMBIC_CONFIG = None


@bagbunker.group()
def admin():
    """Administrative tasks"""
    global ALEMBIC_CONFIG
    from alembic import config
    ini = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'alembic.ini')
    ALEMBIC_CONFIG = config.Config(ini)


@admin.command()
@click.option('--quiet/--no-quiet')
@click.pass_context
def checkdb(ctx, quiet):
    if STORAGE is None:
        if not quiet:
            click.utils.echo("Database not initialized, run 'bagbunker admin initdb'")
        ctx.exit(2)
    else:
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(ALEMBIC_CONFIG)
        latest_rev = script.get_current_head()
        current_rev = db.session.execute('SELECT version_num FROM alembic_version')\
                                .first()[0]
        if current_rev != latest_rev:
            if not quiet:
                click.utils.echo("Database schema outdated - needs migration!")
            ctx.exit(9)
    if not quiet:
        click.utils.echo("Database initialized and up-to-date - all good!")


@admin.command()
@click.pass_context
def initdb(ctx):
    """Initialize database, dropping all tables"""
    app = ctx.obj
    if STORAGE:
        ctx.fail("Database already initialized.")

    db.create_all()

    if not app.config.get('USE_SQLITE'):
        from alembic import command
        command.stamp(ALEMBIC_CONFIG, 'head')

    uuid = Storage.new_storage().uuid
    with open(UUID_FILE, 'wb') as f:
        f.write(uuid)


# @admin.command('purge-jobruns')
# @click.confirmation_option(help='Are you sure you want to purge old jobruns?')
def purge_jobruns():
    """Purge olde jobruns"""

    def remove_dir(logger, d):
        try:
            os.rmdir(d)
            logger.debug('Removed empty directory: %s', d)
        except OSError, e:
            if e.strerror == 'Directory not empty':
                logger.debug('Keeping non-empty directory: %s', d)
            else:
                logger.error('Removing %r: %r', d, e.strerror)

    # XXX: Move into jobrun directory manager or such to implement locking

    # delete models of outdated jobs
    to_delete = set()
    for ids in Jobrun.query.with_entities(db.func.array_agg(Jobrun.id))\
                           .group_by(Jobrun.name, Jobrun.fileset_id):
        ids = ids[0]
        ids.sort()
        to_delete.update(ids[:-1])

    if to_delete:
        Jobfile.query.filter(Jobfile.jobrun_id.in_(to_delete))\
                     .delete(synchronize_session=False)
        Jobrun.query.filter(Jobrun.id.in_(to_delete))\
                    .delete(synchronize_session=False)
        db.session.commit()

    # By now, all job ids that do still exists are valid and their
    # directories should be kept.
    valid_ids = set(x[0] for x in Jobrun.query.with_entities(Jobrun.id))
    logger = logging.getLogger('bagbunker.purge-jobruns')
    jobruns_dir = os.path.join(flask.current_app.instance_path, 'jobruns')
    deleted = []
    for category in os.listdir(jobruns_dir):
        catdir = os.path.join(jobruns_dir, category)
        logger.debug('Entering category directory: %s', catdir)
        for job in os.listdir(catdir):
            jobdir = os.path.join(catdir, job)
            logger.debug('Entering job directory: %s', jobdir)
            for jobrunid in os.listdir(jobdir):
                jobrundir = os.path.join(jobdir, jobrunid)
                try:
                    jobrunid = int(jobrunid)
                except ValueError:
                    logger.error('Not a jobrun dir: %s', jobrundir)
                    continue
                if jobrunid in valid_ids:
                    logger.debug('Keeping jobrun dir: %s', jobrundir)
                else:
                    logger.debug('Removing jobrun dir: %s', jobrundir)
                    deleted.append(jobrundir)
                    shutil.rmtree(jobrundir)
            remove_dir(logger, jobdir)
        remove_dir(logger, catdir)
    logger.info('Deleted %s jobrun dirs', len(deleted))


@bagbunker.command()
@click.option('--read-pending/--no-read-pending',
              help='Read pending filesets after scan')
@click.option('--run-all-jobs/--no-run-all-jobs',
              help='Run all jobs on new filesets')
@click.argument('directories', nargs=-1, required=True,
                type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.pass_context
def scan(ctx, directories, read_pending, run_all_jobs):
    """Scan one or more base directories for filesets"""
    STORAGE.scan_all(directories)
    if read_pending:
        ctx.invoke(_read_pending)
    if run_all_jobs:
        ctx.invoke(run_jobs, all=True)


@bagbunker.command(name='read-pending')
def _read_pending():
    """Read pending filesets"""
    STORAGE.read_pending()


# The future
class RunJobs(click.MultiCommand):
    def list_commands(self, ctx):
        return JOB.keys()

    def get_command(self, ctx, name):
        job = JOB[name]
        params = [click.Option(['--{}'.format(x.name.replace('_', '-'))],
                               # show_default=True,  does not display configured
                               default=x.default)
                  for x in job.configs]
        return click.Command(name=name, callback=job, params=params)


@bagbunker.command(name='run-jobs', cls=RunJobs, invoke_without_command=True)
@click.option('--all/--no-all')
@click.option('--force/--no-force')
@click.option('--fileset', multiple=True,
              help='Only run job(s) for specific fileset (name/md5)')
@click.option('--job', multiple=True, help='Specify job, may be used multiple times.')
@click.pass_context
def run_jobs(ctx, all, force, fileset, job):
    """Run jobs for read filesets - slower
    """
    logger = logging.getLogger('bagbunker.run-jobs')
    logger.setLevel(logging.INFO)
    app = ctx.obj
    db.create_all()
    storage = STORAGE
    jobconfig = read_config(os.path.join(ctx.obj.instance_path, 'job.cfg'))

    if not ctx.invoked_subcommand and not all and not job:
        click.echo(ctx.command.get_help(ctx))
        ctx.exit()

    if ctx.invoked_subcommand:
        joblist = [ctx.invoked_subcommand]
    elif job:
        joblist = job   # multiple
    else:
        joblist = filter(None, jobconfig.get('job', {}).get('list', '').split(' ')) \
            or JOB.keys()
    cmdlist = [(JOB[name].inputs[0].topics, ctx.command.get_command(ctx, name))
               for name in joblist]

    if not cmdlist:
        print "No jobs to run"
        ctx.exit()

    MATRIX = OrderedDict()
    filesets = storage.active_intact_filesets\
                      .filter(Fileset.read_succeeded.is_(True))
    if fileset:
        fileset_filter = reduce(lambda x, y: x | y, (
            ((Fileset.name == x) | (Fileset.md5.like('{}%'.format(x))))
            for x in fileset   # multiple
        ))
        filesets = filesets.filter(fileset_filter)
    for fileset in filesets:
        bag = fileset.bag
        if bag is None:
            continue
        fileset_topics = set([x.topic.name for x in bag.topics])
        topics = set()
        cmds = []
        jobruns = Jobrun.query.filter(Jobrun.fileset == fileset)
        # jobruns may be aborted - in this case they neither succeeded not failed
        # We could create them as failed
        # We could not add them to the DB until they are done
        latest = dict(jobruns.with_entities(Jobrun.name, db.func.max(Jobrun.version))
                      .filter(Jobrun.succeeded.is_(True) | Jobrun.failed.is_(True))
                      .group_by(Jobrun.name))
        for cmdtopics, cmd in cmdlist:
            if not force and cmd.name in latest and \
               cmd.callback.version <= latest[cmd.name]:
                continue

            # XXX: hack for jobs that don't want messages
            if not cmdtopics:
                cmds.append(((), cmd))
                continue

            intersect = fileset_topics.intersection(cmdtopics)
            if intersect:
                topics = topics.union(intersect)
                cmds.append((cmdtopics, cmd))
        if cmds:
            MATRIX[fileset] = topics, cmds

    if not MATRIX:
        ctx.exit()

    # for each fileset, start all registered jobs in parallel - at
    # this point we know that topics a job wants do exist
    for fileset, (topics, cmds) in MATRIX.items():
        logger.info('Starting job run for fileset %s', fileset.name)
        async_jobs = [make_async_job(app=app, name=cmd.name,
                                     topics=cmdtopics,
                                     job=partial(ctx.invoke, cmd),
                                     group=cmd.callback.namespace,
                                     version=cmd.callback.version,
                                     fileset_id=fileset.id,
                                     config=jobconfig.get(cmd.name, {}))
                      for cmdtopics, cmd in cmds]
        logger.info('Created threads for: %s', [x.name for x in async_jobs])
        milkers = []
        for async_job in async_jobs:
            name = async_job.thread.name
            thread = Thread(target=async_job_milker, name=name,
                            args=(app, async_job,))
            thread.daemon = True
            thread.start()
            milkers.append(thread)

        def messages():
            if not topics:
                return
            import rosbag
            for file in fileset.files:
                rbag = rosbag.Bag(file.path)
                for msg in rbag.read_messages(topics=topics):
                    yield msg

        for msg in messages():
            for async_job in async_jobs:
                # XXX: replace with namedtuple
                topic, _, _ = msg
                if topic in async_job.topics:
                    async_job.msg_queue.put(msg)

        for async_job in async_jobs:
            async_job.msg_queue.put(Done)

        for milker in milkers:
            milker.join()

    # Never call subcommand directly
    ctx.exit()


@bagbunker.command('webserver')
@click.option('--cors/--no-cors', default=True)
@click.option('--wdb/--no-wdb', default=False)
@click.option('--public/--no-public', default=False)
@click.option('--verbose-request-logging/--no-verbose-request-logging')
@click.pass_obj
def webserver(app, cors, wdb, public, verbose_request_logging):
    """Start a development webserver server
    """
    if cors:
        from flask.ext.cors import CORS
        CORS(app)
    kw = dict(debug=True)
    if public:
        kw['host'] = '0.0.0.0'
    if wdb:
        from wdb.ext import WdbMiddleware
        app.wsgi_app = WdbMiddleware(app.wsgi_app)
        kw['use_debugger'] = False  # Disable builtin Werkzeug debugger
    if verbose_request_logging:
        app.logger.setLevel(logging.DEBUG)
        app.config['LOG_REQUESTS'] = True
    app.run(reloader_type='watchdog', **kw)


def cli():
    # from ipdb import launch_ipdb_on_exception
    # with launch_ipdb_on_exception():
    #     bagbunker(auto_envvar_prefix='MARV')
    bagbunker(auto_envvar_prefix='MARV')


if __name__ == '__main__':
    cli()
