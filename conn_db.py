import psycopg2

def connect():
    connection = psycopg2.connect(
        database="Course_app",
        user="postgres",
        password="Zasada0902_2000",
        host="localhost",
        port="5432",
    )
    return connection

def close_db_connect(connection, cursor):
    cursor.close()
    connection.close()
