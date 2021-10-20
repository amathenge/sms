from flask import g
import sqlite3


def connect_db():
    # remember to use the following line in production
    # sql = sqlite3.connect('/home/fairacresltd/sms/message.db')
    sql = sqlite3.connect('message.db')
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
