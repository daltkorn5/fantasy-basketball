import psycopg2
import os


def _get_connection_params():
    home_dir = os.getenv("HOME")
    with open(f"{home_dir}/.pgpass", 'r') as fp:
        entries = [entry.strip() for entry in fp.readlines()]

    # the second record in the pgpass file is the one for the NBA database
    return entries[1].split(":")


def _get_conn():
    host, port, db, user, password = _get_connection_params()
    return psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)


def insert(query, values):
    with _get_conn() as conn:
        with conn.cursor() as cur:
            if type(values) == list:
                cur.executemany(query, values)
            else:
                cur.execute(query, values)

            conn.commit()
