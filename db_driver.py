import string
import random
import psycopg2


handle = "localhost"
# handle = "34.93.181.52"
database = "telio_lions"


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
          "password text;"
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
          "ClickDates date[], " \
          "UploadDates date[], " \
          "Latitudes text[], " \
          "Longitudes text[], " \
          "Faces bytea[], " \
          "Whiskers bytea[], " \
          "LEars bytea[], " \
          "REars byte[], " \
          "LEyes byte[], " \
          "REyes byte[], " \
          "Noses byte[];"
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
