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

import bcrypt
import flask
import flask.ext.compress
import flask.ext.login
import flask.ext.restless
import flask.ext.restless.search
import flask.ext.sqlalchemy
import json
import logging
import os

from . import api_messages
from . import filter as _       # noqa
from . import monkeypatch as _  # noqa
from . import view as _         # noqa
from .filtering import filter_config, filter_query
from .frontend import frontend
from .listing import generate_listing_model, populate_listing_cache
from .listing import get_local_listing, set_remote_listing, serialize_listing_entry
from .logrequest import logrequest
from .model import db, Comment, File, Fileset, Jobrun, Storage, Tag, User

from .registry import load_formats, load_jobs   # noqa
from .serializer import fileset_detail, fileset_summary


apimanager = flask.ext.restless.APIManager()


def create_app(config_obj, **kw):
    logger = logging.getLogger(__name__)
    logger.debug('creating app from {config_obj} and {kw}'
                 .format(config_obj=config_obj, kw=kw))
    instance_path = kw.pop('INSTANCE_PATH', None)
    app = flask.Flask(__name__, instance_path=instance_path,
                      instance_relative_config=True)

    # XXX: is config able to change the instance directory? In that
    # case we need to be further down alongside FILE_STORAGE_PATH
    #if not os.path.exists(app.instance_path):
    #    os.makedirs(app.instance_path)

    app.config['FILE_STORAGE_PATH'] = os.path.join(app.instance_path, 'storage')
    app.config['FRONTEND_PATH'] = os.path.join(app.instance_path, 'frontend', 'dist')

    app.config.from_object(config_obj)               # default settings
    app.config.from_pyfile('app.cfg', silent=True)   # instance-specific config
    app.config.update(kw)                            # call-specific overrides

    # Should only be used for testing
    if app.config.get('USE_SQLITE'):
        app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///{path}/_db.sqlite'.format(path=app.instance_path)

    if app.config.get('USE_X_SENDFILE'):
        app.use_x_sendfile = True

    app.config['SQLALCHEMY_BINDS'] = {'cache': 'sqlite://'}

    #if not os.path.exists(app.config['FILE_STORAGE_PATH']):
    #    os.makedirs(app.config['FILE_STORAGE_PATH'])

    login_manager = flask.ext.login.LoginManager()
    login_manager.init_app(app)
    app.secret_key = 'secret key'

    compress = flask.ext.compress.Compress()
    compress.init_app(app)
    db.init_app(app)
    apimanager.init_app(app, flask_sqlalchemy_db=db)

    # TODO: factor this out to auth_file or auth_ldap or ...
    def authenticate(username, password):
        usersfile = os.sep.join([app.instance_path, 'users.txt'])
        with open(usersfile) as f:
            users = dict(x.strip().split(':') for x in f.readlines())

        hashed = users.get(username, '')
        if not hashed:
            return False

        hashed = '$2a$' + hashed[4:]
        return bcrypt.hashpw(password, hashed) == hashed

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    @app.errorhandler(500)
    def handle_500(e):
        app.logger.error(e)
        if hasattr(e, 'get_description'):
            message = e.get_description()
        else:
            message = str(e)
        return flask.jsonify({'error': message})

    @app.route('/marv/api/_login', methods=['GET', 'POST'])
    def login():
        if flask.ext.login.current_user.is_authenticated:
            username = flask.ext.login.current_user.username
            userid = flask.ext.login.current_user.id
            return flask.jsonify({'username': username, 'id': userid})

        if flask.request.method != 'POST':
            return flask.jsonify({'username': None, 'id': None})

        username = flask.request.form.get('username', '')
        password = flask.request.form.get('password', '')
        if authenticate(username, password):
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(username=username)
                db.session.add(user)
                db.session.commit()
            flask.ext.login.login_user(user, remember=True)
        else:
            return flask.jsonify({'username': None, 'id': None})
        return flask.jsonify({'username': username, 'id': user.id})

    @app.route('/marv/api/_logout')
    @flask.ext.login.login_required
    def logout():
        flask.ext.login.logout_user()
        return '', 200

    @app.route('/marv/api/_tag', methods=['POST'])
    @flask.ext.login.login_required
    def tag():
        req = flask.request.get_json()
        if req is None:
            return flask.abort(400)
        fileset_id = req.get('fileset_id')
        fileset = Fileset.query.get(fileset_id) if fileset_id is not None else None
        if fileset is None:
            return flask.abort(400)
        if req.get('tag_id'):
            tag = Tag.query.get(req['tag_id'])
            if tag is None:
                return flask.abort(400)
        elif req.get('tag_label'):
            tag = Tag.query.filter_by(label=req['tag_label']).first()
            if tag is None:
                tag = Tag(label=req['tag_label'])
        else:
            return flask.abort(400)

        if fileset not in tag.filesets:
            tag.filesets.append(fileset)
        db.session.add(tag)
        db.session.commit()

        return flask.jsonify({'label': tag.label, 'id': tag.id})

    @app.route('/marv/api/_untag', methods=['POST'])
    @flask.ext.login.login_required
    def untag():
        req = flask.request.get_json()
        fileset = Fileset.query.get(req['fileset_id'])
        if fileset is None:
            return flask.abort(400)

        if req.get('tag_id'):
            tag = Tag.query.get(req['tag_id'])
            if tag is None:
                return flask.abort(400)
        elif req.get('tag_label'):
            tag = Tag.query.filter_by(label=req['tag_label']).first()
            if tag is None:
                return flask.abort(400)
        else:
            return flask.abort(400)

        if fileset in tag.filesets:
            tag.filesets.remove(fileset)
            if len(tag.filesets):
                db.session.add(tag)
            else:
                db.session.delete(tag)
            db.session.commit()

        return flask.jsonify({})

    @app.route('/marv/api/_webconfig')
    def foo():
        return flask.jsonify({
            'filters': filter_config()
        })

    def filtered_fileset():
        filters = flask.request.args.get('filter', '{}')

        try:
            filters = json.loads(filters)
        except ValueError:
            return flask.abort(400)

        return filter_query(db.session.query(ListingEntry), filters)

    @app.route('/marv/api/_fileset-summary')
    def fileset_summary_route():
        entries = filtered_fileset().filter(ListingEntry.remote.is_(None))
        ids = [x.fileset_id for x in entries]
        entries = db.session.query(Fileset).filter(Fileset.id.in_(ids))
        return flask.jsonify(fileset_summary(entries))

    @app.route('/marv/api/_fileset-listing')
    def fileset_listing_route():
        return flask.jsonify({
            'sort': 'endtime',
            'ascending': False,
            'rows': [serialize_listing_entry(r) for r in filtered_fileset()]
        })

    @app.route('/marv/api/_fileset/<int:fileset_id>', methods=['DELETE'])
    @flask.ext.login.login_required
    def fileset_delete_route(fileset_id):
        fileset = db.session.query(Fileset).filter(Fileset.id == fileset_id).one()
        fileset.deleted = True
        fileset.deleted_reason = flask.ext.login.current_user.username
        db.session.commit()
        return flask.jsonify({})

    @app.route('/marv/jobrun/<path:filename>')
    def jobrun(filename):
        jobrundir = os.path.join(app.instance_path, 'jobruns')
        return flask.send_from_directory(jobrundir, filename)

    @app.route('/marv/listing', methods=['GET'])
    def get_listing():
        res = {}
        res[flask.request.headers.get('Host')] = get_local_listing()
        return flask.jsonify(res)

    @app.route('/marv/listing', methods=['POST'])
    def set_listing():
        listing = flask.request.get_json()
        return flask.jsonify(set_remote_listing(listing))

    @app.route('/marv/download/<path:md5>')
    def download(md5):
        file = (db.session
                .query(File)
                .filter(File.md5 == md5)
                .join(Fileset)
                .filter(Fileset.deleted.op('IS NOT')(True))
                .first())
        return flask.send_from_directory(file.fileset.dirpath, file.name,
                                         as_attachment=True,
                                         attachment_filename=file.name)

    def auth_func(**kw):
        if not flask.ext.login.current_user.is_authenticated:
            raise flask.ext.restless.ProcessingException(
                description='Not Authorized', code=401)

    with app.app_context():
        # Create Listing model
        ListingEntry, Relations = generate_listing_model()

        # Create API endpoints, which will be available at /api/<tablename> by
        # default. Allowed HTTP methods can be specified as well.
        kw = {'app': app, 'url_prefix': '/marv/api'}
        apimanager.create_api(Storage, **kw)
        apimanager.create_api(ListingEntry, **kw)
        for rel in Relations.values():
            apimanager.create_api(rel, **kw)
        apimanager.create_api(File,
                              max_page_size=1000,
                              page_size=1000,
                              **kw)

        apimanager.create_api(Tag, **kw)
        apimanager.create_api(User, primary_key='id', **kw)
        apimanager.create_api(Comment, methods=['GET', 'POST'],
                              preprocessors=dict(POST=[auth_func]), **kw)

        # private API for communication with web frontend
        apimanager.create_api(Fileset, serializer=fileset_detail,
                              collection_name='_fileset-detail', **kw)
        apimanager.create_api(Fileset, serializer=fileset_detail,
                              collection_name='_fileset-detail-by-md5',
                              primary_key='md5', **kw)
        # has to come after custom serializers for JSONAPI
        apimanager.create_api(Fileset,
                              max_page_size=1000,
                              page_size=1000,
                              **kw)
        apimanager.create_api(Jobrun, **kw)

        from bagbunker.model import Bag
        apimanager.create_api(Bag, **kw)

    app.register_blueprint(frontend)
    app.register_blueprint(logrequest)
    app.register_blueprint(api_messages.api)

    import pkg_resources
    for ep in pkg_resources.iter_entry_points(group='marv_apps'):
        MarvApp = ep.load()
        marvapp = MarvApp(url_prefix='/marv/apps/{}'.format(ep.name))
        marvapp.init_app(app)

    return app
