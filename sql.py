# -*- coding: utf-8 -*-
import sqlite3 as lite
from sqlite3 import Error
 
 
def create_connection(db_file):
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        conn.close()
 
if __name__ == '__main__':
    curr=lite.connect("C:\\sqlite\db3\pythonsqlite.db")
    cur=curr.cursor()
    cur.execute("CREATE TABLE stocks (word_id integer, trans text, symbol text,qty real,price real)")
    cur.execute("INSERT INTO stocks VALUES('2006­01­05','BUY','RHAT',100,3514)") 
    cur.execute("INSERT INTO stocks VALUES('2006­01­05','BUYING','RHAT',100,3514)") 
    curr.commit()
    curr.close()
