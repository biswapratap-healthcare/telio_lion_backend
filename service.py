import os
import shutil
import tempfile
import time
import zipfile
from datetime import datetime, timezone

from waitress import serve
from flask_cors import CORS
from flask import Flask, send_file

from werkzeug.utils import secure_filename
from flask_restplus import Resource, Api, reqparse
from werkzeug.datastructures import FileStorage

from db_driver import login, create_new_user, modify_password, if_table_exists, create_lion_data_table, \
    create_user_data_table, truncate_table, drop_table
from lion_model import LionDetection
from utils import on_board_new_lion


def current_milli_time():
    return round(time.time() * 1000)


def store_and_verify_file(file_from_request, work_dir):
    if not file_from_request.filename:
        return -1, 'Empty file part provided!'
    try:
        file_path = os.path.join(work_dir, secure_filename(file_from_request.filename))
        if os.path.exists(file_path) is False:
            file_from_request.save(file_path)
        return 0, file_path
    except Exception as ex:
        return -1, str(ex)


def upload_and_verify_file(file_from_request, work_dir):
    if not file_from_request.filename:
        return -1, 'Empty file part provided!', None
    try:
        fn = str(current_milli_time()) + '_' + secure_filename(file_from_request.filename)
        file_path = os.path.join(work_dir, fn)
        if os.path.exists(file_path) is False:
            file_from_request.save(file_path)
        return 0, file_path, fn
    except Exception as ex:
        return -1, str(ex), None


def init():
    if not if_table_exists(table_name='user_data'):
        create_user_data_table()
    if not if_table_exists(table_name='lion_data'):
        create_lion_data_table()


def create_app():
    # init()
    app = Flask("foo", instance_relative_config=True)

    api = Api(
        app,
        version='1.0.0',
        title='TelioLabs Lion Backend App',
        description='TelioLabs Lion Backend App',
        default='TelioLabs Lion Backend App',
        default_label=''
    )

    CORS(app)

    onboard_parser = reqparse.RequestParser()
    onboard_parser.add_argument('payload',
                                location='files',
                                type=FileStorage,
                                help='A zip of dirs, where each dir name is a lion name and '
                                     'each dir content is a set of lion images',
                                required=True)

    @api.route('/on_board_new_lions')
    @api.expect(onboard_parser)
    class OnboardService(Resource):
        @api.expect(onboard_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = onboard_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status_codes'] = '-1'
                rv['status_strings'] = str(e)
                return rv, 404
            extract_dir = None
            download_dir = None
            try:
                status_codes = ''
                status_strings = ''
                file_from_request = args['payload']
                extract_dir = tempfile.mkdtemp()
                download_dir = tempfile.mkdtemp()
                ret, file_path_or_status = store_and_verify_file(file_from_request, download_dir)
                if ret == 0:
                    zip_handle = zipfile.ZipFile(file_path_or_status, "r")
                    zip_handle.extractall(path=extract_dir)
                    zip_handle.close()
                    data_dir = os.path.join(extract_dir, 'test_data')
                    _dirs = os.listdir(data_dir)
                    for _dir in _dirs:
                        _lion_name = _dir
                        d = os.path.join(data_dir, _lion_name)
                        _lion_images = os.listdir(d)
                        _lion_id = str(current_milli_time())
                        ret, status = on_board_new_lion(_lion_id, _lion_name, d, _lion_images)
                        status_codes = status_codes + str(ret) + ','
                        status_strings = status_strings + status + ', '
                else:
                    rv = dict()
                    rv['status_codes'] = '-1'
                    rv['status_strings'] = file_path_or_status
                    if extract_dir:
                        shutil.rmtree(extract_dir)
                    if download_dir:
                        shutil.rmtree(download_dir)
                    return rv, 404
                rv = dict()
                rv['status_codes'] = status_codes[:-1]
                rv['status_strings'] = status_strings[:-1]
                if extract_dir:
                    shutil.rmtree(extract_dir)
                if download_dir:
                    shutil.rmtree(download_dir)
                return rv, 200
            except Exception as e:
                if extract_dir:
                    shutil.rmtree(extract_dir)
                if download_dir:
                    shutil.rmtree(download_dir)
                rv = dict()
                rv['status_codes'] = '-1'
                rv['status_strings'] = str(e)
                return rv, 404

    drop_table_parser = reqparse.RequestParser()
    drop_table_parser.add_argument('table_name',
                                   type=str,
                                   help='The Table to be destroyed/dropped',
                                   required=True)

    @api.route('/drop_table')
    @api.expect(drop_table_parser)
    class DropTableService(Resource):
        @api.expect(drop_table_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = drop_table_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                table_name = args['table_name']
                if if_table_exists(table_name=table_name):
                    ret, status = drop_table(table_name)
                else:
                    status = table_name + " doesn't exist!"
                    ret = -1
                rv = dict()
                rv['status'] = status
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    truncate_table_parser = reqparse.RequestParser()
    truncate_table_parser.add_argument('table_name',
                                       type=str,
                                       help='The Table to be truncated',
                                       required=True)

    @api.route('/truncate_table')
    @api.expect(truncate_table_parser)
    class TruncateTableService(Resource):
        @api.expect(truncate_table_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = truncate_table_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                table_name = args['table_name']
                if if_table_exists(table_name=table_name):
                    ret, status = truncate_table(table_name)
                else:
                    status = table_name + " doesn't exist!"
                    ret = -1
                rv = dict()
                rv['status'] = status
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    user_login_parser = reqparse.RequestParser()
    user_login_parser.add_argument('un',
                                   type=str,
                                   help='User Name',
                                   required=True)
    user_login_parser.add_argument('pw',
                                   type=str,
                                   help='Password',
                                   required=True)

    @api.route('/user_login')
    @api.expect(user_login_parser)
    class UserLoginService(Resource):
        @api.expect(user_login_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = user_login_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                _un = args['un']
                _pw = args['pw']
                ret = login(_un, _pw)
                rv = dict()
                if ret == 0:
                    rv['status'] = "Login Success"
                    return rv, 200
                else:
                    rv['status'] = "Login Failed"
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    create_new_user_parser = reqparse.RequestParser()
    create_new_user_parser.add_argument('name',
                                        type=str,
                                        help='Name',
                                        required=True)
    create_new_user_parser.add_argument('id',
                                        type=str,
                                        help='ID Number',
                                        required=True)
    create_new_user_parser.add_argument('un',
                                        type=str,
                                        help='User Name',
                                        required=True)

    @api.route('/create_new_user')
    @api.expect(create_new_user_parser)
    class CreateNewUserService(Resource):
        @api.expect(create_new_user_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = create_new_user_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                _name = args['name']
                _id = args['id']
                _un = args['un']
                ret, status = create_new_user(_name, _id, _un)
                rv = dict()
                rv['status'] = status
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    modify_password_parser = reqparse.RequestParser()
    modify_password_parser.add_argument('un',
                                        type=str,
                                        help='User Name',
                                        required=True)
    modify_password_parser.add_argument('old_pw',
                                        type=str,
                                        help='Old Password',
                                        required=True)
    modify_password_parser.add_argument('new_pw',
                                        type=str,
                                        help='New Password',
                                        required=True)

    @api.route('/modify_password')
    @api.expect(modify_password_parser)
    class ModifyPasswordService(Resource):
        @api.expect(modify_password_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = modify_password_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                _un = args['un']
                _old_pw = args['old_pw']
                _new_pw = args['new_pw']
                ret, status = modify_password(_un, _old_pw, _new_pw)
                rv = dict()
                rv['status'] = status
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    health_check_parser = reqparse.RequestParser()
    health_check_parser.add_argument('var',
                                     type=int,
                                     help='dummy variable',
                                     required=True)

    @api.route('/health_check')
    @api.expect(health_check_parser)
    class HealthCheckService(Resource):
        @api.expect(health_check_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = health_check_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            rv = dict()
            rv['health'] = "good"
            return rv, 200

    return app


if __name__ == "__main__":
    serve(create_app(), host='0.0.0.0', port=8000, threads=20)
