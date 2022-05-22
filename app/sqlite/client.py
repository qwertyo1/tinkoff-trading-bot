import sqlite3


class SQLiteClient:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)

    def close(self):
        self.conn.close()

    def execute(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.fetchall()

    def execute_insert(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.lastrowid

    def execute_update(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount

    def execute_delete(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount

    def execute_select(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def execute_select_one(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()
