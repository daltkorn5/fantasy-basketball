from typing import List, Dict, Any

import psycopg2
from psycopg2.extras import DictCursor
import os


class QueryTool:
    """Class to facilitate interactions with the PostgreSQL database in which all the data is stored"""

    @staticmethod
    def _get_connection_params() -> List[str]:
        """Gets the connection information for the NBA database

        :return: The connection information for the NBA database
        """
        home_dir = os.getenv("HOME")
        with open(f"{home_dir}/.pgpass", 'r') as fp:
            entries = [entry.strip() for entry in fp.readlines()]

        # the second record in the pgpass file is the one for the NBA database
        return entries[1].split(":")

    def _get_connection(self):
        """Creates the connection to the database

        :return: The database connection
        """
        host, port, db, user, password = self._get_connection_params()
        return psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)

    def insert(self, query, values=None) -> None:
        """Runs an insert query against the database

        Also can be used for "upsert" queries

        :param query: The query you want to run
        :param values: The values that will be inserted into the database
        """
        if values is None:
            values = {}

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if type(values) == list:
                    cur.executemany(query, values)
                else:
                    cur.execute(query, values)

                conn.commit()

    def select(self, query, params=None) -> List[Dict[str, Any]]:
        """Runs a select query against the database

        :param query: The query you want to run
        :param params: Any parameters that you want to use with the query
        :return: The results of the query as a list of dicts
        """
        if params is None:
            params = {}

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        return [dict(row) for row in rows]

    def delete(self, query, params=None) -> None:
        """Runs a delete query against the database

        :param query: The query you want to run
        :param params: Any parameters that you want to use with the query
        """
        if params is None:
            params = {}

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)

            conn.commit()
