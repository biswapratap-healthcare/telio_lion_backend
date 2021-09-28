import string
import random
from datetime import datetime, timezone

import psycopg2


handle = "localhost"
# handle = "34.93.181.52"
database = "telio_lions"


def get_bytes(image):
    image_bytes = b''
    with open(image, "rb") as f:
        byte = f.read(1)
        while byte:
            image_bytes += byte
            byte = f.read(1)
    return image_bytes


def insert_lion_data(_id, name, click_date, image, face, whisker, lear, rear, leye, reye, nose):
    ret = 0
    status = "Success"
    conn = None
    try:
        upload_date = datetime.now(timezone.utc)
        click_date = upload_date
        image_bytes = get_bytes(image)
        face_bytes = get_bytes(face)
        whisker_bytes = get_bytes(whisker)
        lear_bytes = get_bytes(lear)
        rear_bytes = get_bytes(rear)
        leye_bytes = get_bytes(leye)
        reye_bytes = get_bytes(reye)
        nose_bytes = get_bytes(nose)

        sql = """INSERT INTO lion_data VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING ID;"""
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (_id,
                          name,
                          click_date,
                          upload_date,
                          '0.0',
                          '0.0',
                          image_bytes,
                          face_bytes,
                          whisker_bytes,
                          lear_bytes,
                          rear_bytes,
                          leye_bytes,
                          reye_bytes,
                          nose_bytes,))
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
          "id text, " \
          "name text, " \
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
    sql = "CREATE TABLE lion_data (ID text PRIMARY KEY, " \
          "Name text, " \
          "ClickDate date, " \
          "UploadDate date, " \
          "Latitude text, " \
          "Longitude text, " \
          "Image bytea, " \
          "Face bytea, " \
          "Whisker bytea, " \
          "LEar bytea, " \
          "REar bytea, " \
          "LEye bytea, " \
          "REye bytea, " \
          "Nose bytea);"
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


def update_user_parameter(un, var_name, var_value):
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
        cur.execute(sql, (var_value, un,))
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


def modify_password(_un, _old_pw, _new_pw):
    ret = login(_un, _old_pw)
    if ret is True:
        ret_str, ret = update_user_parameter(_un, 'password', _new_pw)
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
            if str(record[1]) != pwd:
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


def create_new_user(_name, _id, _un):
    ret = 0
    status = "Success"
    conn = None
    sql = """INSERT INTO user_data(name, id, username, password) VALUES(%s,%s,%s,%s) RETURNING username;"""
    try:
        n = 10
        _pwd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (_name, _id, _un, _pwd,))
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
    finally:
        if conn is not None:
            conn.close()
        return ret, status
