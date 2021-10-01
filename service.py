import os
import shutil
import tempfile
import zipfile

from waitress import serve
from flask_cors import CORS
from flask import Flask

from werkzeug.utils import secure_filename
from flask_restplus import Resource, Api, reqparse
from werkzeug.datastructures import FileStorage

from db_driver import login, create_new_user, modify_password, if_table_exists, create_lion_data_table, \
    create_user_data_table, truncate_table, drop_table, get_lion_name_info, get_lion_id_info, get_data, \
    update_lion_name_parameter, update_user_parameter, delete_user, delete_lion_name, delete_lion_id, get_current_count
from utils import on_board_new_lion, current_milli_time, check_upload


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
    init()
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

    @api.route('/get_count')
    class GetCountService(Resource):
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                ret, r = get_current_count()
                if r == 0:
                    return ret, 200
                else:
                    return ret, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    delete_lion_id_parser = reqparse.RequestParser()
    delete_lion_id_parser.add_argument('username',
                                       type=str,
                                       help='An admin user name',
                                       required=True)
    delete_lion_id_parser.add_argument('lion_id',
                                       type=str,
                                       help='The instance of lion id to be deleted',
                                       required=True)

    @api.route('/delete_lion_id')
    @api.expect(delete_lion_id_parser)
    class DeleteLionIDService(Resource):
        @api.expect(delete_lion_id_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = delete_lion_id_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            try:
                username = args['username']
                lion_id = args['lion_id']
                ret_str, ret = delete_lion_id(username, lion_id)
                rv = dict()
                rv['status'] = ret_str
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    delete_lion_name_parser = reqparse.RequestParser()
    delete_lion_name_parser.add_argument('username',
                                         type=str,
                                         help='An admin user name',
                                         required=True)
    delete_lion_name_parser.add_argument('lion_name',
                                         type=str,
                                         help='All the instances of lion name to be deleted',
                                         required=True)

    @api.route('/delete_lion_name')
    @api.expect(delete_lion_name_parser)
    class DeleteLionNameService(Resource):
        @api.expect(delete_lion_name_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = delete_lion_name_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            try:
                username = args['username']
                lion_name = args['lion_name']
                ret_str, ret = delete_lion_name(username, lion_name)
                rv = dict()
                rv['status'] = ret_str
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    delete_user_parser = reqparse.RequestParser()
    delete_user_parser.add_argument('username1',
                                    type=str,
                                    help='In case an admin is deleting username2, '
                                         'then the admin username, else optional',
                                    required=False)
    delete_user_parser.add_argument('username2',
                                    type=str,
                                    help='The username to be deleted',
                                    required=True)
    delete_user_parser.add_argument('password2',
                                    type=str,
                                    help='The password of the username to be deleted, if admin then optional',
                                    required=False)

    @api.route('/delete_user')
    @api.expect(delete_user_parser)
    class DeleteUserService(Resource):
        @api.expect(delete_user_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = delete_user_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            try:
                try:
                    username1 = args['username1']
                    if username1 is None:
                        username1 = ''
                except Exception as e:
                    username1 = ''
                username2 = args['username2']
                try:
                    password2 = args['password2']
                    if password2 is None:
                        password2 = ''
                except Exception as e:
                    password2 = ''
                ret_str, ret = delete_user(username1, username2, password2)
                rv = dict()
                rv['status'] = ret_str
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    edit_user_data_parser = reqparse.RequestParser()
    edit_user_data_parser.add_argument('user_name',
                                       type=str,
                                       help='The user name',
                                       required=True)
    edit_user_data_parser.add_argument('param_name',
                                       type=str,
                                       help='The param name - name or email or phone or role',
                                       required=True)
    edit_user_data_parser.add_argument('param_value',
                                       type=str,
                                       help='The param value',
                                       required=True)
    edit_user_data_parser.add_argument('password',
                                       type=str,
                                       help='The password (Optional, if role is admin) ',
                                       required=False)

    @api.route('/edit_user_data')
    @api.expect(edit_user_data_parser)
    class EditUserDataService(Resource):
        @api.expect(edit_user_data_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = edit_user_data_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            try:
                user_name = args['user_name']
                param_name = args['param_name']
                param_value = args['param_value']
                try:
                    password = args['password']
                    if password is None:
                        password = ''
                except Exception as e:
                    password = ''
                ret_str, ret = update_user_parameter(user_name, password, param_name, param_value)
                rv = dict()
                rv['status'] = ret_str
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    edit_lion_status_parser = reqparse.RequestParser()
    edit_lion_status_parser.add_argument('lion_name',
                                         type=str,
                                         help='The lion name',
                                         required=True)
    edit_lion_status_parser.add_argument('lion_status',
                                         type=str,
                                         help='The lion status, A - Alive or D - Dead',
                                         required=True)

    @api.route('/edit_lion_status')
    @api.expect(edit_lion_status_parser)
    class EditLionStatusService(Resource):
        @api.expect(edit_lion_status_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = edit_lion_status_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            try:
                lion_name = args['lion_name']
                lion_status = args['lion_status']
                ret_str, ret = update_lion_name_parameter(lion_name, 'status', lion_status)
                rv = dict()
                rv['status'] = ret_str
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    edit_lion_sex_parser = reqparse.RequestParser()
    edit_lion_sex_parser.add_argument('lion_name',
                                      type=str,
                                      help='The lion name',
                                      required=True)
    edit_lion_sex_parser.add_argument('lion_sex',
                                      type=str,
                                      help='The lion sex, M - Male or F - Female or U - Unknown',
                                      required=True)

    @api.route('/edit_lion_sex')
    @api.expect(edit_lion_sex_parser)
    class EditLionSexService(Resource):
        @api.expect(edit_lion_sex_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = edit_lion_sex_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            try:
                lion_name = args['lion_name']
                lion_sex = args['lion_sex']
                ret_str, ret = update_lion_name_parameter(lion_name, 'sex', lion_sex)
                rv = dict()
                rv['status'] = ret_str
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('offset',
                            type=int,
                            help='Offset from which records needs to be read',
                            required=True)
    get_parser.add_argument('count',
                            type=int,
                            help='Number of records to be read from offset',
                            required=True)

    @api.route('/list')
    @api.expect(get_parser)
    class ListService(Resource):
        @api.expect(get_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = get_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['health'] = str(e)
                return rv, 404
            try:
                offset = args['offset']
                count = args['count']
                rv, ret = get_data(offset, count)
                if ret != 0:
                    return rv, 404
                else:
                    return rv, 200
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    get_lion_id_info_parser = reqparse.RequestParser()
    get_lion_id_info_parser.add_argument('lion_id',
                                         type=str,
                                         help='The lion id',
                                         required=True)

    @api.route('/get_lion_id_info')
    @api.expect(get_lion_id_info_parser)
    class GetLionIDInfoService(Resource):
        @api.expect(get_lion_id_info_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = get_lion_id_info_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                lion_id = args['lion_id']
                rv, ret = get_lion_id_info(lion_id)
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    get_lion_name_info_parser = reqparse.RequestParser()
    get_lion_name_info_parser.add_argument('lion_name',
                                           type=str,
                                           help='The lion name',
                                           required=True)

    @api.route('/get_lion_name_info')
    @api.expect(get_lion_name_info_parser)
    class GetLionNameInfoService(Resource):
        @api.expect(get_lion_name_info_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = get_lion_name_info_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            try:
                lion_name = args['lion_name']
                rv, ret = get_lion_name_info(lion_name)
                if ret == 0:
                    return rv, 200
                else:
                    return rv, 404
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

    check_upload_parser = reqparse.RequestParser()
    check_upload_parser.add_argument('payload',
                                     location='files',
                                     type=FileStorage,
                                     help='A zip of lion images',
                                     required=True)

    @api.route('/check_upload')
    @api.expect(check_upload_parser)
    class CheckUploadService(Resource):
        @api.expect(check_upload_parser)
        @api.doc(responses={"response": 'json'})
        def post(self):
            try:
                args = check_upload_parser.parse_args()
            except Exception as e:
                rv = dict()
                rv['status'] = str(e)
                return rv, 404
            extract_dir = None
            download_dir = None
            try:
                file_from_request = args['payload']
                extract_dir = tempfile.mkdtemp()
                download_dir = tempfile.mkdtemp()
                ret, file_path_or_status = store_and_verify_file(file_from_request, download_dir)
                if ret == 0:
                    zip_handle = zipfile.ZipFile(file_path_or_status, "r")
                    zip_handle.extractall(path=extract_dir)
                    zip_handle.close()
                    _payload_dir = os.path.join(extract_dir, 'check_payload')
                    _lion_images = os.listdir(_payload_dir)
                    rv = dict()
                    rv['status'] = []
                    for _lion_image in _lion_images:
                        _lion_image_path = os.path.join(_payload_dir, _lion_image)
                        ret = check_upload(_lion_image_path)
                        rv['status'].append({'image': _lion_image, 'ret': ret})
                    if extract_dir:
                        shutil.rmtree(extract_dir)
                    if download_dir:
                        shutil.rmtree(download_dir)
                    return rv, 200
                else:
                    rv = dict()
                    rv['status'] = file_path_or_status
                    if extract_dir:
                        shutil.rmtree(extract_dir)
                    if download_dir:
                        shutil.rmtree(download_dir)
                    return rv, 404
            except Exception as e:
                if extract_dir:
                    shutil.rmtree(extract_dir)
                if download_dir:
                    shutil.rmtree(download_dir)
                rv = dict()
                rv['status'] = str(e)
                return rv, 404

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
                rv['status'] = str(e)
                return rv, 404
            extract_dir = None
            download_dir = None
            try:
                file_from_request = args['payload']
                extract_dir = tempfile.mkdtemp()
                download_dir = tempfile.mkdtemp()
                ret, file_path_or_status = store_and_verify_file(file_from_request, download_dir)
                if ret == 0:
                    zip_handle = zipfile.ZipFile(file_path_or_status, "r")
                    zip_handle.extractall(path=extract_dir)
                    zip_handle.close()
                    _payload_dir = os.path.join(extract_dir, 'onboard_payload')
                    _lions = os.listdir(_payload_dir)
                    rv = dict()
                    rv['status'] = []
                    for _lion in _lions:
                        _lion_dir = os.path.join(_payload_dir, _lion)
                        on_board_new_lion(_lion, _lion_dir, rv)
                    if extract_dir:
                        shutil.rmtree(extract_dir)
                    if download_dir:
                        shutil.rmtree(download_dir)
                    return rv, 200
                else:
                    rv = dict()
                    rv['status'] = file_path_or_status
                    if extract_dir:
                        shutil.rmtree(extract_dir)
                    if download_dir:
                        shutil.rmtree(download_dir)
                    return rv, 404
            except Exception as e:
                if extract_dir:
                    shutil.rmtree(extract_dir)
                if download_dir:
                    shutil.rmtree(download_dir)
                rv = dict()
                rv['status'] = str(e)
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
                if ret is True:
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
    create_new_user_parser.add_argument('email',
                                        type=str,
                                        help='Email of user',
                                        required=True)
    create_new_user_parser.add_argument('phone',
                                        type=str,
                                        help='Phone number of user',
                                        required=True)
    create_new_user_parser.add_argument('role',
                                        type=str,
                                        help='Roles - admin, user',
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
                _email = args['email']
                _phone = args['phone']
                _role = args['role']
                _un = args['un']
                pwd, ret, status = create_new_user(_name, _email, _phone, _role, _un)
                rv = dict()
                rv['status'] = status
                rv['password'] = pwd
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
