import psycopg2
import settings

hostname = settings.DB_SETTINGS['host']
username = settings.DB_SETTINGS['user']
password = settings.DB_SETTINGS['password']
database = settings.DB_SETTINGS['db']

def query_database(query, values = ()):
    conn = psycopg2.connect( host=hostname, user=username, password=password, dbname=database )
    cur = conn.cursor()
    if values:
        cur.execute(query, values)
        conn.commit()
    else:
        cur.execute(query)
        conn.commit()
    try:
        rows = cur.fetchall()
        conn.close()
        return rows
    except:
        conn.close()
        return