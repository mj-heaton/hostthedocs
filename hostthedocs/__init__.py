import os
import json

from flask import abort, Flask, jsonify, redirect, render_template, request, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

from . import getconfig, util
from .filekeeper import delete_files, insert_link_to_latest, parse_docfiles, unpack_project

app = Flask(__name__, static_folder=None)

app.config['MAX_CONTENT_LENGTH'] = getconfig.max_content_mb * 1024 * 1024
auth = HTTPBasicAuth()
try:
    with open(getconfig.user_db) as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

if len(users.keys()) == 0:
    print("Warning, no users found. Please create one with the --user and --password arguments.", flush=True)


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

@app.route('/static/<path:filename>')
@auth.login_required(optional=not getconfig.enable_basic_auth)
def send_docs(filename):
    print("Serving file: %s" % filename, flush=True)
    return send_from_directory('static', filename)


@app.route('/hmfd', methods=['POST', 'DELETE'])
@auth.login_required(optional=not getconfig.enable_basic_auth)
def hmfd():
    if getconfig.readonly:
        return abort(403)

    if request.method == 'POST':
        if not request.files:
            return abort(400, 'Request is missing a zip/tar file.')
        uploaded_file = util.file_from_request(request)
        unpack_project(
            uploaded_file,
            request.form,
            getconfig.docfiles_dir
        )
        uploaded_file.close()
    elif request.method == 'DELETE':
        if getconfig.disable_delete:
            return abort(403)

        delete_files(
            request.args['name'],
            request.args.get('version'),
            getconfig.docfiles_dir,
            request.args.get('entire_project'))
    else:
        abort(405)

    return jsonify({'success': True})


@app.route('/')
@auth.login_required(optional=not getconfig.enable_basic_auth)
def home():
    projects = parse_docfiles(getconfig.docfiles_dir, getconfig.docfiles_link_root)
    insert_link_to_latest(projects, '%(project)s/latest')
    return render_template('index.html', projects=projects, **getconfig.renderables)


@app.route('/<project>/latest/')
@auth.login_required(optional=not getconfig.enable_basic_auth)
def latest_root(project):
    return latest(project, '')


@app.route('/<project>/latest/<path:path>')
@auth.login_required(optional=not getconfig.enable_basic_auth)
def latest(project, path):
    parsed_docfiles = parse_docfiles(getconfig.docfiles_dir, getconfig.docfiles_link_root)
    proj_for_name = dict((p['name'], p) for p in parsed_docfiles)
    if project not in proj_for_name:
        return 'Project %s not found' % project, 404
    latestindex = proj_for_name[project]['versions'][-1]['link']
    if path:
        latestlink = '%s/%s' % (os.path.dirname(latestindex), path)
    else:
        latestlink = latestindex
    return redirect('/' + latestlink)
