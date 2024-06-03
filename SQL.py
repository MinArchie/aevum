import sqlite3
from sqlite3 import Error

def create_connection(db_file):
	conn = None
	try:
		conn = sqlite3.connect(db_file)
		return conn
	except Error as e:
		print(e)
	return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_object(path):
	conn = create_connection(path)
	c = conn.cursor()
	return c
def main():

	sql_create_users_table = """CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uname TEXT NOT NULL UNIQUE,
        era TEXT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        bio TEXT
    );"""

	sql_create_posts_table = """CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uname TEXT NOT NULL,
    era TEXT NOT NULL,
	title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image TEXT,
    likes INTEGER DEFAULT 0,
    FOREIGN KEY(uname) REFERENCES user(uname)
);"""


	conn = create_connection("time_travel.db")

	if conn is not None:
		create_table(conn, sql_create_users_table)
		create_table(conn, sql_create_posts_table)
	else:
		print("Error! Cannot create database connection")

	print("Users")
	l=conn.execute("SELECT * from user")
	for row in l:
		print (row)
	print("posts")
	l=conn.execute("SELECT * from posts")
	for row in l:
		print (row)
	conn.close()


if __name__ == '__main__':
	main()