import base64
import string
import random
from scipy import spatial
from datetime import datetime, timezone

import psycopg2

from config import is_whiskers

handle = "localhost"
# handle = "34.93.181.52"
database = "telio_lions"


def get_base64_str(image):
    with open(image, "rb") as imageFile:
        base64_str = str(base64.b64encode(imageFile.read()))
    return base64_str


def get_current_count():
    ret = dict()
    r = 0
    male_lions = 0
    female_lions = 0
    unknown_sex_lions = 0
    alive_lions = 0
    dead_lions = 0
    conn = None
    sql = "SELECT sex, status FROM lion_data;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        records = cur.fetchall()
        cur.close()
        total_lions = len(records)
        for record in records:
            sex = record[0]
            status = record[1]
            if sex == 'M':
                male_lions += 1
            elif sex == 'F':
                female_lions += 1
            else:
                unknown_sex_lions += 1
            if status == 'D':
                dead_lions += 1
            else:
                alive_lions += 1
        ret['total'] = str(total_lions)
        ret['male'] = str(male_lions)
        ret['female'] = str(female_lions)
        ret['unknown_sex'] = str(unknown_sex_lions)
        ret['alive'] = str(alive_lions)
        ret['dead'] = str(dead_lions)
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = dict()
        r = -1
    finally:
        if conn is not None:
            conn.close()
        return ret, r


def get_user_parameter(username, parameter_name):
    ret = 0
    ret_str = ""
    conn = None
    sql = "SELECT " + parameter_name + " FROM user_data WHERE username = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (username,))
        records = cur.fetchall()
        cur.close()
        if len(records) == 1:
            ret_str = str(records[0][0])
        else:
            ret = -1
            ret_str = 'Not Found'
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def delete_lion_id(username, lion_id):
    role, ret = get_user_parameter(username, 'role')
    if role != 'admin':
        return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "DELETE FROM lion_data WHERE id = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_id,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def delete_lion_name(username, lion_name):
    role, ret = get_user_parameter(username, 'role')
    if role != 'admin':
        return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "DELETE FROM lion_data WHERE name = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_name,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def delete_user(username1, username2, password2):
    role, ret = get_user_parameter(username1, 'role')
    if role != 'admin':
        ret = login(username2, password2)
        if ret is False:
            return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "DELETE FROM user_data WHERE username = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (username2,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def update_user_parameter(username, password, var_name, var_value):
    role, ret = get_user_parameter(username, 'role')
    if role != 'admin':
        ret = login(username, password)
        if ret is False:
            return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "UPDATE user_data SET " + var_name + " = %s WHERE username = %s;"

    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (var_value, username,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def update_lion_name_parameter(lion_name, var_name, var_value):
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "UPDATE lion_data SET " + var_name + " = %s WHERE lion_name = %s;"

    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (var_value, lion_name,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def get_data(offset, count):
    rv = dict()
    ret = 0
    conn = None
    sql = """SELECT * FROM lion_data OFFSET %s ROWS FETCH FIRST %s ROW ONLY;"""

    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (offset, count,))
        records = cur.fetchall()
        for idx, record in enumerate(records):
            one_record = dict()
            one_record['id'] = record[0]
            one_record['name'] = record[1]
            one_record['sex'] = record[2]
            one_record['status'] = record[3]
            one_record['click_date'] = str(record[4])
            one_record['upload_date'] = str(record[5])
            one_record['latitude'] = record[6]
            one_record['longitude'] = record[7]
            # one_record['image'] = record[8]
            # one_record['face'] = record[9]
            # one_record['whisker'] = record[10]
            # one_record['l_ear'] = record[11]
            # one_record['r_ear'] = record[12]
            # one_record['l_eye'] = record[13]
            # one_record['r_eye'] = record[14]
            # one_record['nose'] = record[15]
            rv[str(idx)] = one_record
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
        rv = dict()
    finally:
        if conn is not None:
            conn.close()
        return rv, ret


def get_lion_id_info(lion_id):
    rv = dict()
    ret = 0
    conn = None
    sql = "SELECT * FROM lion_data WHERE id = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_id,))
        records = cur.fetchall()
        if len(records) != 1:
            ret = -1
        else:
            record = records[0]
            rv['id'] = record[0]
            rv['name'] = record[1]
            rv['sex'] = record[2]
            rv['status'] = record[3]
            rv['click_date'] = str(record[4])
            rv['upload_date'] = str(record[5])
            rv['latitude'] = record[6]
            rv['longitude'] = record[7]
            # rv['image'] = record[8]
            rv['face'] = record[9]
            rv['whisker'] = record[10]
            rv['l_ear'] = record[11]
            rv['r_ear'] = record[12]
            rv['l_eye'] = record[13]
            rv['r_eye'] = record[14]
            rv['nose'] = record[15]
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret


def get_lion_name_info(lion_name):
    rv = dict()
    ret = 0
    conn = None
    sql = "SELECT * FROM lion_data WHERE name = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_name,))
        records = cur.fetchall()
        for idx, record in enumerate(records):
            one_record = dict()
            one_record['id'] = record[0]
            one_record['name'] = record[1]
            one_record['sex'] = record[2]
            one_record['status'] = record[3]
            one_record['click_date'] = str(record[4])
            one_record['upload_date'] = str(record[5])
            one_record['latitude'] = record[6]
            one_record['longitude'] = record[7]
            # one_record['image'] = record[8]
            one_record['face'] = record[9]
            one_record['whisker'] = record[10]
            one_record['l_ear'] = record[11]
            one_record['r_ear'] = record[12]
            one_record['l_eye'] = record[13]
            one_record['r_eye'] = record[14]
            one_record['nose'] = record[15]
            rv[str(idx)] = one_record
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret


def get_all_lion_embeddings():
    ret = list()
    conn = None
    sql = "SELECT id, name, face_embedding, whisker_embedding FROM lion_data;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        ret = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = list()
    finally:
        if conn is not None:
            conn.close()
        return ret


def match_lion(face_embedding, whisker_embedding):
    ret = dict()
    match_data = list()
    embeddings = get_all_lion_embeddings()
    face_embedding = [float(x) for x in face_embedding.split(',')]
    whisker_embedding = [float(x) for x in whisker_embedding.split(',')]

    for embedding in embeddings:
        ref_id = embedding[0]
        ref_lion_name = embedding[1]
        ref_face_embedding = [float(x) for x in embedding[2].split(',')]
        ref_whisker_embedding = [float(x) for x in embedding[3].split(',')]
        face_distance = spatial.distance.cosine(ref_face_embedding, face_embedding)
        whisker_distance = spatial.distance.cosine(ref_whisker_embedding, whisker_embedding)
        match_data.append((ref_id, ref_lion_name, face_distance, whisker_distance))

    if is_whiskers:
        index = 3
    else:
        index = 2
    match_data.sort(key=lambda x: x[index])

    if len(match_data) > 0:
        _1st_match = match_data[0]
        d_1st = _1st_match[index]
        if d_1st < 0.10:
            ret['type'] = 'Similar'
            ret['similar'] = [{'id': _1st_match[0], 'name': _1st_match[1]}]
        elif d_1st > 0.10 and d_1st < 0.25:
            ret['type'] = 'New'
        elif d_1st > 0.25:
            ret['type'] = 'Not'
        else:
            ret['type'] = 'Not'
    if len(match_data) > 1:
        _2nd_match = match_data[1]
        d_2nd = _2nd_match[index]
        if d_2nd < 0.10:
            ret['similar'].append({'id': _2nd_match[0], 'name': _2nd_match[1]})
    if len(match_data) > 2:
        _3rd_match = match_data[2]
        d_3rd = _3rd_match[index]
        if d_3rd < 0.10:
            ret['similar'].append({'id': _3rd_match[0], 'name': _3rd_match[1]})
    return ret


def insert_lion_data(_id, name,
                     sex, life_status,
                     utc_click_datetime,
                     lat, lon,
                     image, face,
                     whisker, lear,
                     rear, leye,
                     reye, nose,
                     face_embedding,
                     whisker_embedding):
    ret = 0
    status = "Success"
    conn = None
    try:
        upload_date = datetime.now(timezone.utc)
        click_date = utc_click_datetime
        try:
            image_bytes = get_base64_str(image)
        except Exception as e:
            image_bytes = ''
            pass
        face_bytes = get_base64_str(face)
        whisker_bytes = get_base64_str(whisker)
        try:
            lear_bytes = get_base64_str(lear)
        except Exception as e:
            lear_bytes = ''
            pass
        try:
            rear_bytes = get_base64_str(rear)
        except Exception as e:
            rear_bytes = ''
            pass
        try:
            leye_bytes = get_base64_str(leye)
        except Exception as e:
            leye_bytes = ''
            pass
        try:
            reye_bytes = get_base64_str(reye)
        except Exception as e:
            reye_bytes = ''
            pass
        try:
            nose_bytes = get_base64_str(nose)
        except Exception as e:
            nose_bytes = ''
            pass

        sql = """INSERT INTO lion_data VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING ID;"""
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (_id,
                          name,
                          sex,
                          life_status,
                          click_date,
                          upload_date,
                          lat,
                          lon,
                          image_bytes,
                          face_bytes,
                          whisker_bytes,
                          lear_bytes,
                          rear_bytes,
                          leye_bytes,
                          reye_bytes,
                          nose_bytes,
                          face_embedding,
                          whisker_embedding))
        _id = cur.fetchone()[0]
        if _id:
            conn.commit()
            print("Committed --> " + str(_id))
        else:
            ret = -1
            status = "Failed to insert lion data."
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
        status = str(error)
    finally:
        if conn is not None:
            conn.close()
        return ret, status


def drop_table(table_name):
    ret = 0
    status = "Success"
    conn = None
    sql = "DROP TABLE " + table_name + ";"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        status = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret, status


def truncate_table(table_name):
    ret = 0
    status = "Success"
    conn = None
    sql = "TRUNCATE " + table_name + ";"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        status = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret, status


def create_user_data_table():
    ret = 0
    status = "Success"
    conn = None
    sql = "CREATE TABLE user_data (username text PRIMARY KEY, " \
          "name text, " \
          "email text, " \
          "phone text, " \
          "role text, " \
          "password text);"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        status = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret, status


def create_lion_data_table():
    ret = 0
    status = "Success"
    conn = None
    sql = "CREATE TABLE lion_data (id text PRIMARY KEY, " \
          "name text, " \
          "sex text, " \
          "status text, " \
          "click_date date, " \
          "upload_date date, " \
          "latitude text, " \
          "longitude text, " \
          "image text, " \
          "face text, " \
          "whisker text, " \
          "l_ear text, " \
          "r_ear text, " \
          "l_eye text, " \
          "r_eye text, " \
          "nose text, " \
          "face_embedding text, " \
          "whisker_embedding text);"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        status = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret, status


def if_table_exists(table_name='lion_data'):
    ret = False
    conn = None
    sql = "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '" + table_name + "');"""
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        ret = cur.fetchone()[0]
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = False
    finally:
        if conn is not None:
            conn.close()
        return ret


def modify_password(_un, _old_pw, _new_pw):
    ret = login(_un, _old_pw)
    if ret is True:
        ret_str, ret = update_user_parameter(_un, _old_pw, 'password', _new_pw)
    else:
        ret_str = "Invalid existing password."
        ret = -1
    return ret, ret_str


def login(un, pwd):
    ret = True
    conn = None
    sql = """select password from user_data where username = %s"""
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (un,))
        record = cur.fetchall()
        if len(record) != 1:
            ret = False
        else:
            record = record[0]
            if str(record[0]) != pwd:
                ret = False
            else:
                ret = True
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = False
    finally:
        if conn is not None:
            conn.close()
        return ret


def create_new_user(_name, _email, _phone, _role, _un):
    ret = 0
    status = "Success"
    conn = None
    _pwd = ''
    sql = """INSERT INTO user_data(username, name, email, phone, role, password) 
             VALUES(%s,%s,%s,%s,%s,%s) RETURNING username;"""
    try:
        n = 10
        _pwd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (_un, _name, _email, _phone, _role, _pwd,))
        un = cur.fetchone()[0]
        if un:
            conn.commit()
            print("Committed --> " + str(un))
        else:
            ret = -1
            status = "Failed to commit."
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
        status = str(error)
        _pwd = ''
    finally:
        if conn is not None:
            conn.close()
        return _pwd, ret, status
